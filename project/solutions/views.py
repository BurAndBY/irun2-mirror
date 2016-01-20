from collections import namedtuple

from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.views import generic
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, render, render_to_response
from django.db import transaction
from django.template import RequestContext
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse


from .forms import AdHocForm
from .models import AdHocRun, Solution, Judgement, Rejudge, TestCaseResult, JudgementLog, Outcome
from .actions import enqueue_new
from .tables import SolutionTable
from .permissions import SolutionPermissions
from common.views import LoginRequiredMixin
from table.views import FeedDataView

from storage.storage import ResourceId, create_storage
from storage.utils import serve_resource, serve_resource_metadata

from common.views import IRunnerListView
from proglangs.utils import get_highlightjs_class
from django.http import Http404


class TestCaseResultMixin(object):
    def serve_testcaseresult_page(self, request, testcaseresult, data_url_pattern, item_id):
        limit = 2**12
        storage = create_storage()
        context = {
            'testcaseresult': testcaseresult,
            'data_url_pattern': data_url_pattern,
            'item_id': item_id,
            'input_repr': storage.represent(testcaseresult.input_resource_id, limit=limit),
            'output_repr': storage.represent(testcaseresult.output_resource_id, limit=limit),
            'answer_repr': storage.represent(testcaseresult.answer_resource_id, limit=limit),
            'stdout_repr': storage.represent(testcaseresult.stdout_resource_id, limit=limit),
            'stderr_repr': storage.represent(testcaseresult.stderr_resource_id, limit=limit),
        }
        template_name = 'solutions/testcaseresult.html'
        return render(request, template_name, context)

    def serve_testcaseresult_data(self, request, mode, testcaseresult):
        resource_id = {
            'input': testcaseresult.input_resource_id,
            'output': testcaseresult.output_resource_id,
            'answer': testcaseresult.answer_resource_id,
            'stdout': testcaseresult.stdout_resource_id,
            'stderr': testcaseresult.stderr_resource_id,
        }.get(mode)

        return serve_resource(request, resource_id, 'text/plain')


class AdHocView(generic.View):
    template_name = 'solutions/ad_hoc.html'

    def get(self, request, *args, **kwargs):
        form = AdHocForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = AdHocForm(request.POST)
        judgement_id = None

        if form.is_valid():

            storage = create_storage()
            f = ContentFile(form.cleaned_data['input_data'].encode('utf-8'))
            resource_id = storage.save(f)

            run = AdHocRun(
                resource_id=resource_id,
                input_file_name='input.txt',
                output_file_name='output.txt',
                time_limit=2000,
                memory_limit=0,
            )

            run.save()

            f = ContentFile(form.cleaned_data['source_code'].encode('utf-8'))
            resource_id = storage.save(f)

            solution = Solution(
                ad_hoc_run=run,
                resource_id=resource_id,
                compiler=form.cleaned_data['compiler'],
                filename='',
            )

            solution.save()

            judjement = enqueue_new(solution)
            judgement_id = judjement.id

            #form.save()
            #return HttpResponseRedirect(reverse('problems:index'))

        return render(request, self.template_name, {'form': form, 'judgement_id': judgement_id})


class SolutionListView(IRunnerListView):
    paginate_by = 25

    def get_queryset(self):
        return Solution.objects.prefetch_related('compiler').select_related('best_judgement').select_related('source_code')


'''
Judgement
'''


class JudgementView(generic.View):
    template_name = 'solutions/judgement.html'

    def get(self, request, judgement_id):
        judgement = get_object_or_404(Judgement, pk=judgement_id)
        test_results = judgement.testcaseresult_set.all()

        storage = create_storage()
        logs = [storage.represent(log.resource_id) for log in JudgementLog.objects.filter(judgement_id=judgement.id)]

        permissions = SolutionPermissions.all()

        return render(request, self.template_name, {
            'judgement': judgement,
            'logs': logs,
            'test_results': test_results,
            'solution_permissions': permissions,
        })


class JudgementTestCaseResultView(TestCaseResultMixin, generic.View):
    template_name = 'solutions/testcaseresult.html'

    def get(self, request, judgement_id, testcaseresult_id):
        testcaseresult = get_object_or_404(TestCaseResult, judgement_id=judgement_id, id=testcaseresult_id)
        return self.serve_testcaseresult_page(request, testcaseresult, 'solutions:judgement_testdata', judgement_id)


class JudgementTestCaseResultDataView(TestCaseResultMixin, generic.View):
    def get(self, request, judgement_id, testcaseresult_id, mode):
        testcaseresult = get_object_or_404(TestCaseResult, judgement_id=judgement_id, id=testcaseresult_id)
        return self.serve_testcaseresult_data(request, mode, testcaseresult)


'''
Rejudge
'''


class CreateRejudgeView(generic.View):
    def get(self, request, *args, **kwargs):
        ids = request.GET.getlist('id')
        return render(request, 'solutions/confirm_multiple.html', {'ids': ids})

    def post(self, request, *args, **kwargs):
        ids = request.GET.getlist('id')
        with transaction.atomic():
            rejudge = Rejudge.objects.create()
            judgements = [Judgement(solution_id=solution_id, rejudge=rejudge) for solution_id in ids]
            Judgement.objects.bulk_create(judgements)

        return HttpResponseRedirect(reverse('solutions:rejudge', args=[rejudge.id]))


RejudgeInfo = namedtuple('RejudgeInfo', ['solution', 'before', 'after'])


class RejudgeView(generic.View):
    def get(self, request, rejudge_id):
        rejudge = get_object_or_404(Rejudge, pk=rejudge_id)
        object_list = []
        for new_judgement in rejudge.judgement_set.all().select_related('solution').select_related('solution__best_judgement'):
            solution = new_judgement.solution
            object_list.append(RejudgeInfo(solution, solution.best_judgement, new_judgement))

        return render(request, 'solutions/rejudge.html', {'committed': rejudge.committed, 'object_list': object_list})

    def post(self, request, rejudge_id):
        need_commit = ('commit' in request.POST)
        need_rollback = ('rollback' in request.POST)

        if (need_commit ^ need_rollback):
            target = True if need_commit else False
            num_rows = Rejudge.objects.filter(id=rejudge_id, committed=None).update(committed=target)
            if num_rows and need_commit:
                with transaction.atomic():
                    rejudge = get_object_or_404(Rejudge, pk=rejudge_id)
                    for new_judgement in rejudge.judgement_set.all().select_related('solution'):
                        solution = new_judgement.solution
                        solution.best_judgement = new_judgement
                        solution.save()

        return HttpResponseRedirect(reverse('solutions:rejudge', args=[rejudge_id]))


def ilist(request):
    objects = Solution.objects.all().prefetch_related('compiler').select_related('best_judgement')
    table = SolutionTable(objects)
    #return render(request, "solutions/ilist.html", {'table': table})
    return render_to_response("solutions/ilist.html", {"table": table},
                              context_instance=RequestContext(request))


class BaseSolutionView(LoginRequiredMixin, generic.View):
    tab = None

    def _load(self, request, solution_id):
        solution = get_object_or_404(Solution, pk=solution_id)
        permissions = SolutionPermissions()
        return solution, permissions

    def _require(self, value):
        if not value:
            raise PermissionDenied()

    def _make_context(self, solution, permissions, extra=None):
        context = {
            'solution': solution,
            'solution_permissions': permissions,
            'active_tab': self.tab,
        }
        if extra is not None:
            context.update(extra)
        return context

    def get(self, request, solution_id, *args, **kwargs):
        self.solution, self.permissions = self._load(request, solution_id)
        result = self.do_get(request, self.solution, self.permissions, *args, **kwargs)
        return result

    def do_get(self, *args, **kwargs):
        raise NotImplementedError()


class SolutionSourceView(BaseSolutionView):
    tab = 'source'
    template_name = 'solutions/solution_source.html'

    def do_get(self, request, solution, permissions):
        self._require(permissions.source_code)

        storage = create_storage()
        source_repr = storage.represent(solution.source_code.resource_id)

        context = self._make_context(solution, permissions, {
            'language': get_highlightjs_class(solution.compiler.language),
            'source_repr': source_repr,
        })
        return render(request, self.template_name, context)


class SolutionTestsView(BaseSolutionView):
    tab = 'tests'
    template_name = 'solutions/solution_tests.html'

    def do_get(self, request, solution, permissions):
        self._require(permissions.results)

        test_results = solution.best_judgement.testcaseresult_set.all()

        context = self._make_context(solution, permissions, {
            'test_results': test_results
        })
        return render(request, self.template_name, context)


class SolutionJudgementsView(BaseSolutionView):
    tab = 'judgements'
    template_name = 'solutions/solution_judgements.html'

    def do_get(self, request, solution, permissions):
        self._require(permissions.judgements)

        context = self._make_context(solution, permissions, {
            'judgements': solution.judgement_set.all()
        })
        return render(request, self.template_name, context)


class SolutionLogView(BaseSolutionView):
    tab = 'log'
    template_name = 'solutions/solution_log.html'

    def do_get(self, request, solution, permissions):
        self._require(permissions.compilation_log)

        log_repr = None

        if solution.best_judgement is not None:
            judgementlog = solution.best_judgement.judgementlog_set.filter(kind=JudgementLog.SOLUTION_COMPILATION).first()
            if judgementlog is not None:
                storage = create_storage()
                log_repr = storage.represent(judgementlog.resource_id)

        context = self._make_context(solution, permissions, {
            'log_repr': log_repr
        })
        return render(request, self.template_name, context)


class SolutionMainView(BaseSolutionView):
    def do_get(self, request, solution, permissions):
        judgement = solution.best_judgement

        cls = None

        if cls is None and permissions.results:
            if judgement is not None:
                test_results_count = judgement.testcaseresult_set.count()
                if test_results_count > 0:
                    cls = SolutionTestsView

        if cls is None and permissions.compilation_log:
            if judgement is not None:
                cls = SolutionLogView

        if cls is None and permissions.source_code:
            cls = SolutionSourceView

        if cls is None:
            raise PermissionDenied()

        return cls().do_get(request, solution, permissions)


class SolutionStatusJsonView(BaseSolutionView):
    def do_get(self, request, solution, permissions):
        judgement = solution.best_judgement
        if judgement is not None:
            data = {
                'text': judgement.show_status(),
                'final': judgement.status == Judgement.DONE
            }
            if judgement.status == Judgement.DONE:
                data['ok'] = judgement.outcome == Outcome.ACCEPTED
        else:
            data = {
                'text': 'N/A',
                'final': False
            }
        return JsonResponse(data)


class SolutionSourceOpenView(generic.View):
    def get(self, request, solution_id, filename):
        solution = get_object_or_404(Solution, pk=solution_id)
        if filename != solution.source_code.filename:
            raise Http404()

        return serve_resource(request, solution.source_code.resource_id, 'text/plain')


class SolutionSourceDownloadView(generic.View):
    def get(self, request, solution_id, filename):
        solution = get_object_or_404(Solution, pk=solution_id)
        if filename != solution.source_code.filename:
            raise Http404()

        return serve_resource_metadata(request, solution.source_code, force_download=True)


class SolutionTestCaseResultView(TestCaseResultMixin, generic.View):
    template_name = 'solutions/testcaseresult.html'

    def get(self, request, solution_id, testcaseresult_id):
        solution = get_object_or_404(Solution, pk=solution_id)
        if solution.best_judgement is None:
            raise Http404('Solution is not judged')

        testcaseresult = get_object_or_404(TestCaseResult, id=testcaseresult_id, judgement_id=solution.best_judgement_id)
        return self.serve_testcaseresult_page(request, testcaseresult, 'solutions:test_data', solution.id)


class SolutionTestCaseResultDataView(TestCaseResultMixin, generic.View):
    def get(self, request, solution_id, testcaseresult_id, mode):
        solution = get_object_or_404(Solution, pk=solution_id)
        if solution.best_judgement is None:
            raise Http404('Solution is not judged')

        testcaseresult = get_object_or_404(TestCaseResult, id=testcaseresult_id, judgement_id=solution.best_judgement_id)
        return self.serve_testcaseresult_data(request, mode, testcaseresult)

import difflib
from collections import namedtuple

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Count
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import ugettext_lazy, pgettext_lazy
from django.utils.timesince import timesince
from django.views import generic

from cauth.mixins import LoginRequiredMixin, StaffMemberRequiredMixin
from common.pageutils import paginate
from common.views import MassOperationView
from problems.description import IDescriptionImageLoader, render_description
from problems.models import ProblemRelatedFile
from proglangs.utils import get_highlightjs_class
from storage.storage import create_storage
from storage.utils import serve_resource, serve_resource_metadata

from .calcpermissions import calculate_permissions
from .compare import fetch_solution
from .forms import AllSolutionsFilterForm, CompareSolutionsForm
from .models import Solution, Judgement, Rejudge, TestCaseResult, JudgementLog, Outcome
from .permissions import SolutionPermissions
from .utils import create_judgement
from .filters import apply_state_filter, apply_compiler_filter


class DescriptionImageLoader(IDescriptionImageLoader):
    def __init__(self, problem_id):
        self._problem_id = problem_id

    def get_image_list(self):
        return ProblemRelatedFile.objects.\
            filter(problem_id=self._problem_id).\
            filter(file_type__in=ProblemRelatedFile.TEST_CASE_IMAGE_FILE_TYPES).\
            values_list('filename', flat=True)


class TestCaseResultMixin(object):
    def serve_testcaseresult_page(self, testcaseresult, data_url_pattern, image_url_pattern, item_id):
        limit = 2**12
        storage = create_storage()

        context = {
            'test_case_result': testcaseresult,
            'data_url_pattern': data_url_pattern,
            'image_url_pattern': image_url_pattern,
            'item_id': item_id,
            'input_repr': storage.represent(testcaseresult.input_resource_id, limit=limit),
            'output_repr': storage.represent(testcaseresult.output_resource_id, limit=limit),
            'answer_repr': storage.represent(testcaseresult.answer_resource_id, limit=limit),
            'stdout_repr': storage.represent(testcaseresult.stdout_resource_id, limit=limit),
            'stderr_repr': storage.represent(testcaseresult.stderr_resource_id, limit=limit),
        }

        test_case = testcaseresult.test_case
        if test_case is not None:

            loader = DescriptionImageLoader(test_case.problem_id)

            context['test_case'] = test_case
            context['description'] = render_description(test_case.description, loader)

        template_name = 'solutions/testcaseresult.html'
        return render(self.request, template_name, context)

    def serve_testcaseresult_data(self, mode, testcaseresult):
        resource_id = {
            'input': testcaseresult.input_resource_id,
            'output': testcaseresult.output_resource_id,
            'answer': testcaseresult.answer_resource_id,
            'stdout': testcaseresult.stdout_resource_id,
            'stderr': testcaseresult.stderr_resource_id,
        }.get(mode)

        return serve_resource(self.request, resource_id, 'text/plain')

    def serve_testcaseresult_image(self, filename, testcaseresult):
        if testcaseresult.test_case is None:
            raise Http404('Test case result is not associated with a valid test case')

        f = ProblemRelatedFile.objects.\
            filter(problem_id=testcaseresult.test_case.problem_id).\
            filter(file_type__in=ProblemRelatedFile.TEST_CASE_IMAGE_FILE_TYPES).\
            filter(filename=filename).\
            first()
        return serve_resource_metadata(self.request, f)

'''
All solutions list
'''


class SolutionListView(StaffMemberRequiredMixin, generic.View):
    paginate_by = 25
    template_name = 'solutions/solution_list.html'

    def get(self, request):
        form = AllSolutionsFilterForm(request.GET)

        queryset = Solution.objects.\
            prefetch_related('compiler').\
            prefetch_related('problem').\
            prefetch_related('author').\
            select_related('best_judgement').\
            select_related('source_code').\
            order_by('-id')

        if form.is_valid():
            queryset = apply_state_filter(queryset, form.cleaned_data['state'])
            queryset = apply_compiler_filter(queryset, form.cleaned_data['compiler'])

        context = paginate(request, queryset, self.paginate_by)
        context['form'] = form
        return render(request, self.template_name, context)
'''
Judgement
'''


class JudgementListView(StaffMemberRequiredMixin, generic.View):
    paginate_by = 25
    template_name = 'solutions/judgement_list.html'

    def get(self, request):
        queryset = Judgement.objects.select_related('extra_info').order_by('-id')
        context = paginate(request, queryset, self.paginate_by)
        return render(request, self.template_name, context)


class JudgementView(StaffMemberRequiredMixin, generic.View):
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


class JudgementTestCaseResultView(StaffMemberRequiredMixin, TestCaseResultMixin, generic.View):
    template_name = 'solutions/testcaseresult.html'

    def get(self, request, judgement_id, testcaseresult_id):
        testcaseresult = get_object_or_404(TestCaseResult, judgement_id=judgement_id, id=testcaseresult_id)
        return self.serve_testcaseresult_page(testcaseresult, 'solutions:judgement_testdata', 'solutions:judgement_testimage', judgement_id)


class JudgementTestCaseResultDataView(StaffMemberRequiredMixin, TestCaseResultMixin, generic.View):
    def get(self, request, judgement_id, testcaseresult_id, mode):
        testcaseresult = get_object_or_404(TestCaseResult, judgement_id=judgement_id, id=testcaseresult_id)
        return self.serve_testcaseresult_data(mode, testcaseresult)


class JudgementTestCaseResultImageView(StaffMemberRequiredMixin, TestCaseResultMixin, generic.View):
    def get(self, request, judgement_id, testcaseresult_id, filename):
        testcaseresult = get_object_or_404(TestCaseResult, judgement_id=judgement_id, id=testcaseresult_id)
        return self.serve_testcaseresult_image(filename, testcaseresult)

'''
Rejudge
'''


class RejudgeListView(StaffMemberRequiredMixin, generic.ListView):
    template_name = 'solutions/rejudge_list.html'

    def get_queryset(self):
        return Rejudge.objects.all().annotate(num_judgements=Count('judgement')).order_by('-creation_time', '-id')


class CreateRejudgeView(StaffMemberRequiredMixin, MassOperationView):
    template_name = 'solutions/confirm_multiple.html'

    def get_context_data(self, **kwargs):
        context = super(CreateRejudgeView, self).get_context_data(**kwargs)
        context['action'] = pgettext_lazy('verb', 'rejudge')
        return context

    def perform(self, filtered_queryset, form):
        author = self.request.user

        with transaction.atomic():
            rejudge = Rejudge.objects.create(author=author)
            for solution in filtered_queryset:
                create_judgement(solution=solution, rejudge=rejudge)

        return redirect('solutions:rejudge', rejudge.id)

    def get_queryset(self):
        return Solution.objects.order_by('id')


RejudgeInfo = namedtuple('RejudgeInfo', ['solution', 'before', 'after'])


class RejudgeView(StaffMemberRequiredMixin, generic.View):
    template_name = 'solutions/rejudge.html'

    def get(self, request, rejudge_id):
        rejudge = get_object_or_404(Rejudge, pk=rejudge_id)
        object_list = []
        for new_judgement in rejudge.judgement_set.all().\
                select_related('solution').\
                select_related('solution__best_judgement').\
                select_related('solution__author').\
                select_related('solution__source_code').\
                prefetch_related('solution__compiler'):
            solution = new_judgement.solution
            object_list.append(RejudgeInfo(solution, solution.best_judgement, new_judgement))

        context = {
            'rejudge': rejudge,
            'object_list': object_list
        }
        return render(request, self.template_name, context)

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


'''
Mass delete
'''


class DeleteSolutionsView(StaffMemberRequiredMixin, MassOperationView):
    template_name = 'solutions/confirm_multiple.html'

    def get_context_data(self, **kwargs):
        context = super(DeleteSolutionsView, self).get_context_data(**kwargs)
        context['action'] = ugettext_lazy('delete')
        return context

    def perform(self, filtered_queryset, form):
        filtered_queryset.delete()

    def get_queryset(self):
        return Solution.objects.order_by('id')


'''
Single solution
'''


class BaseSolutionView(LoginRequiredMixin, generic.View):
    tab = None
    with_related = True

    def _load_solution(self, solution_id):
        if self.with_related:
            queryset = Solution.objects.\
                select_related('compiler').\
                select_related('best_judgement').\
                select_related('problem').\
                select_related('source_code')
        else:
            queryset = Solution.objects

        return get_object_or_404(queryset, pk=solution_id)

    def _require(self, value):
        if not value:
            raise PermissionDenied()

    def get_context_data(self, **kwargs):
        context = {
            'solution': self.solution,
            'solution_environment': self.environment,
            'solution_permissions': self.permissions,
            'active_tab': self.tab,
        }
        context.update(**kwargs)
        return context

    def get(self, request, solution_id, *args, **kwargs):
        self.solution = self._load_solution(solution_id)
        self.permissions, self.environment = calculate_permissions(self.solution, request.user)

        result = self.do_checked_get(request, self.solution, *args, **kwargs)
        return result

    def do_checked_get(self, *args, **kwargs):
        if not self.is_allowed(self.permissions):
            raise PermissionDenied()
        return self.do_get(*args, **kwargs)

    '''
    methods that must be implemented
    '''

    def is_allowed(self, permissions):
        raise NotImplementedError()

    def do_get(self, request, solution, *args, **kwargs):
        raise NotImplementedError()


class SolutionEmptyView(BaseSolutionView):
    template_name = 'solutions/solution.html'

    def is_allowed(self, permissions):
        return permissions.state

    def do_get(self, request, solution):
        return render(request, self.template_name, self.get_context_data())


class SolutionSourceView(BaseSolutionView):
    tab = 'source'
    template_name = 'solutions/solution_source.html'

    def is_allowed(self, permissions):
        return permissions.source_code

    def do_get(self, request, solution):
        storage = create_storage()
        source_repr = storage.represent(solution.source_code.resource_id)

        context = self.get_context_data()
        context['language'] = get_highlightjs_class(solution.compiler.language)
        context['source_repr'] = source_repr
        return render(request, self.template_name, context)


class SolutionTestsView(BaseSolutionView):
    tab = 'tests'
    template_name = 'solutions/solution_tests.html'

    def is_allowed(self, permissions):
        return permissions.results

    def do_get(self, request, solution):
        test_results = solution.best_judgement.testcaseresult_set.all()
        context = self.get_context_data(test_results=test_results)
        return render(request, self.template_name, context)


class SolutionJudgementsView(BaseSolutionView):
    tab = 'judgements'
    template_name = 'solutions/solution_judgements.html'

    def is_allowed(self, permissions):
        return permissions.judgements

    def do_get(self, request, solution):
        judgements = solution.judgement_set.all()
        context = self.get_context_data(judgements=judgements)
        return render(request, self.template_name, context)


class SolutionLogView(BaseSolutionView):
    tab = 'log'
    template_name = 'solutions/solution_log.html'

    def is_allowed(self, permissions):
        return permissions.compilation_log

    def do_get(self, request, solution):
        log_repr = None

        if solution.best_judgement is not None:
            judgementlog = solution.best_judgement.judgementlog_set.filter(kind=JudgementLog.SOLUTION_COMPILATION).first()
            if judgementlog is not None:
                storage = create_storage()
                log_repr = storage.represent(judgementlog.resource_id)

        context = self.get_context_data(log_repr=log_repr)
        return render(request, self.template_name, context)


AttemptInfo = namedtuple('AttemptInfo', 'number solution active delta pair space')


class SolutionAttemptsView(BaseSolutionView):
    tab = 'attempts'
    template_name = 'solutions/solution_attempts.html'

    def is_allowed(self, permissions):
        return permissions.attempts

    def _calc_visual_space(self, seconds):
        days = seconds / (60. * 60. * 24.)
        if days < 0.5:
            return 0
        return 20 + int(100. * min(days / 7., 1.))

    def do_get(self, request, solution):
        related_solutions = []
        last = None
        number = 0

        for cur in Solution.objects.\
                filter(problem_id=solution.problem_id, author_id=solution.author_id).\
                order_by('reception_time'):
            delta = None
            pair = None
            space = None

            if last is not None:
                delta = timesince(d=last.reception_time, now=cur.reception_time)
                pair = (last.id, cur.id)
                space = self._calc_visual_space((cur.reception_time - last.reception_time).total_seconds())

            number += 1
            related_solutions.append(AttemptInfo(number, cur, (cur == solution), delta, pair, space))

            last = cur

        related_solutions.reverse()

        enable_compare = (len(related_solutions) >= 2)
        context = self.get_context_data(related_solutions=related_solutions, enable_compare=enable_compare)
        return render(request, self.template_name, context)


class SolutionMainView(BaseSolutionView):
    def _get_class(self, request, solution, permissions):
        judgement = solution.best_judgement
        if permissions.results:
            if judgement is not None:
                test_results_count = judgement.testcaseresult_set.count()
                if test_results_count > 0:
                    return SolutionTestsView

        if permissions.compilation_log:
            if judgement is not None:
                return SolutionLogView

        if permissions.source_code:
            return SolutionSourceView

        if permissions.state:
            return SolutionEmptyView

    def do_checked_get(self, *args, **kwargs):
        cls = self._get_class(self.request, self.solution, self.permissions)
        if cls is None:
            raise PermissionDenied()
        # make a copy of self, but use specific class
        instance = cls(
            request=self.request,
            solution=self.solution,
            environment=self.environment,
            permissions=self.permissions,
            args=self.args,
            kwargs=self.kwargs
        )
        return instance.do_checked_get(*args, **kwargs)


class SolutionStatusJsonView(BaseSolutionView):
    with_related = False

    def is_allowed(self, permissions):
        return permissions.state

    def do_get(self, request, solution):
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


class BaseSolutionSourceCodeView(BaseSolutionView):
    '''
    Open/download source code
    '''
    with_related = False

    def is_allowed(self, permissions):
        return permissions.source_code


class SolutionSourceOpenView(BaseSolutionSourceCodeView):
    def do_get(self, request, solution, filename):
        if filename != solution.source_code.filename:
            raise Http404()

        return serve_resource(request, solution.source_code.resource_id, 'text/plain')


class SolutionSourceDownloadView(BaseSolutionSourceCodeView):
    def do_get(self, request, solution, filename):
        if filename != solution.source_code.filename:
            raise Http404()

        return serve_resource_metadata(request, solution.source_code, force_download=True)


class BaseSolutionTestDataView(BaseSolutionView):
    '''
    View test data
    '''
    with_related = False

    def is_allowed(self, permissions):
        return permissions.tests_data


class SolutionTestCaseResultView(TestCaseResultMixin, BaseSolutionTestDataView):
    def do_get(self, request, solution, testcaseresult_id):
        if solution.best_judgement_id is None:
            raise Http404('Solution is not judged')

        testcaseresult = get_object_or_404(TestCaseResult, id=testcaseresult_id, judgement_id=solution.best_judgement_id)
        return self.serve_testcaseresult_page(testcaseresult, 'solutions:test_data', 'solutions:test_image', solution.id)


class SolutionTestCaseResultDataView(TestCaseResultMixin, BaseSolutionTestDataView):
    def do_get(self, request, solution, testcaseresult_id, mode):
        if solution.best_judgement_id is None:
            raise Http404('Solution is not judged')

        testcaseresult = get_object_or_404(TestCaseResult, id=testcaseresult_id, judgement_id=solution.best_judgement_id)
        return self.serve_testcaseresult_data(mode, testcaseresult)


class SolutionTestCaseResultImageView(TestCaseResultMixin, BaseSolutionTestDataView):
    def do_get(self, request, solution, testcaseresult_id, filename):
        if solution.best_judgement_id is None:
            raise Http404('Solution is not judged')

        testcaseresult = get_object_or_404(TestCaseResult, id=testcaseresult_id, judgement_id=solution.best_judgement_id)
        return self.serve_testcaseresult_image(filename, testcaseresult)


'''
Compare two solutions
'''


class CompareSolutionsView(LoginRequiredMixin, generic.View):
    template_name = 'solutions/compare.html'

    def _get_compare_context(self, first_id, second_id):
        first = fetch_solution(first_id, self.request.user)
        second = fetch_solution(second_id, self.request.user)
        ok = (first.text is not None) and (second.text is not None)

        context = {}
        context['first'] = first
        context['second'] = second
        context['has_error'] = not ok
        context['has_result'] = ok

        if ok:
            first_lines = first.text.splitlines()
            second_lines = second.text.splitlines()
            differ = difflib.HtmlDiff(tabsize=4, wrapcolumn=None)
            html = differ.make_table(first_lines, second_lines)
            html = html.replace('<td nowrap="nowrap">', '<td>')
            html = html.replace('&nbsp;', ' ')
            context['difflib_html_content'] = html

        return context

    def get(self, request):
        if request.GET:
            form = CompareSolutionsForm(request.GET)
            if form.is_valid():
                context = self._get_compare_context(form.cleaned_data['first'], form.cleaned_data['second'])
                return render(request, self.template_name, context)
        else:
            form = CompareSolutionsForm()

        # fallback
        context = {'form': form}
        return render(request, self.template_name, context)

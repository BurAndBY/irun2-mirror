from collections import namedtuple

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Count
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import ugettext_lazy, pgettext_lazy
from django.views import generic

from cauth.mixins import LoginRequiredMixin, StaffMemberRequiredMixin
from common.pageutils import paginate
from common.views import MassOperationView
from courses.permissions import calculate_course_solution_access_level
from problems.description import IDescriptionImageLoader, render_description
from problems.models import ProblemRelatedFile
from proglangs.models import Compiler
from proglangs.utils import get_highlightjs_class
from storage.storage import create_storage
from storage.utils import serve_resource, serve_resource_metadata

from .forms import AllSolutionsFilterForm
from .models import Solution, Judgement, Rejudge, TestCaseResult, JudgementLog, Outcome
from .permissions import SolutionPermissions, SolutionAccessLevel
from .utils import create_judgement


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

    state_filters = {
        'waiting': lambda q: q.filter(best_judgement__status=Judgement.WAITING),
        'preparing': lambda q: q.filter(best_judgement__status=Judgement.PREPARING),
        'compiling': lambda q: q.filter(best_judgement__status=Judgement.COMPILING),
        'testing': lambda q: q.filter(best_judgement__status=Judgement.TESTING),
        'finishing': lambda q: q.filter(best_judgement__status=Judgement.FINISHING),
        'done': lambda q: q.filter(best_judgement__status=Judgement.DONE),
        'not-done': lambda q: q.exclude(best_judgement__status=Judgement.DONE),
        'ok': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.ACCEPTED),
        'ce': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.COMPILATION_ERROR),
        'wa': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.WRONG_ANSWER),
        'tle': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.TIME_LIMIT_EXCEEDED),
        'mle': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.MEMORY_LIMIT_EXCEEDED),
        'ile': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.IDLENESS_LIMIT_EXCEEDED),
        'rte': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.RUNTIME_ERROR),
        'pe': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.PRESENTATION_ERROR),
        'sv': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.SECURITY_VIOLATION),
        'cf': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.CHECK_FAILED),
    }

    def _apply_filters(self, queryset, form):
        state_filter = self.state_filters.get(form.cleaned_data['state'])
        if state_filter is not None:
            queryset = state_filter(queryset)

        compiler_value = form.cleaned_data['compiler']
        if compiler_value:
            ok = False
            for language, _ in Compiler.LANGUAGE_CHOICES:
                if language == compiler_value:
                    queryset = queryset.filter(compiler__language=language)
                    ok = True
                    break
            if not ok:
                queryset = queryset.filter(compiler_id=compiler_value)
        return queryset

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
            queryset = self._apply_filters(queryset, form)

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
# course/contest the solution belongs to
SolutionEnvironment = namedtuple('SolutionEnvironment', 'course')


def calculate_permissions(solution, user):
    level = SolutionAccessLevel.NO_ACCESS

    # course
    in_course = calculate_course_solution_access_level(solution, user)
    level = max(level, in_course.level)

    # contest
    # TODO when contests are ready

    permissions = SolutionPermissions()
    permissions.update(level)

    if user.is_staff:
        permissions.set_all()

    return (permissions, SolutionEnvironment(in_course.course))


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

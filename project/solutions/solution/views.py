from collections import namedtuple

from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.encoding import force_text
from django.utils.timesince import timesince
from django.views import generic

from cauth.mixins import LoginRequiredMixin
from common.highlight import list_highlight_styles, get_highlight_style, update_highlight_style
from common.outcome import Outcome
from common.pageutils import paginate
from plagiarism.models import JudgementResult
from storage.storage import create_storage
from storage.utils import serve_resource, serve_resource_metadata

from solutions.mixins import TestCaseResultMixin
from solutions.models import Solution, Judgement, TestCaseResult, JudgementLog

from .calcpermissions import calculate_permissions


class BaseSolutionView(LoginRequiredMixin, generic.View):
    tab = None
    with_related = True

    def _load_solution(self, solution_id):
        if self.with_related:
            queryset = Solution.objects.\
                select_related('compiler').\
                select_related('best_judgement').\
                select_related('best_judgement__extra_info').\
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
        best = self.solution.best_judgement
        if best is not None:
            if hasattr(best, 'extra_info'):
                context['extra_info'] = best.extra_info

        context['attempt_count'] = Solution.objects.filter(problem_id=self.solution.problem_id, author_id=self.solution.author_id).count()
        context['judgement_count'] = Judgement.objects.filter(solution_id=self.solution.id).count()

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
        return permissions.state_on_samples

    def do_get(self, request, solution):
        return render(request, self.template_name, self.get_context_data())


class SolutionSourceView(BaseSolutionView):
    tab = 'source'
    template_name = 'solutions/solution_source.html'

    def is_allowed(self, permissions):
        return permissions.source_code

    def do_get(self, request, solution):
        update_highlight_style(request)

        storage = create_storage()
        source_repr = storage.represent(solution.source_code.resource_id)

        context = self.get_context_data()
        context['highlight_styles'] = list_highlight_styles()
        context['highlight_style'] = get_highlight_style(request)
        context['compiler'] = solution.compiler
        context['source_repr'] = source_repr
        return render(request, self.template_name, context)


class SolutionTestsView(BaseSolutionView):
    tab = 'tests'
    template_name = 'solutions/solution_tests.html'

    def is_allowed(self, permissions):
        return permissions.sample_results or permissions.results

    def do_get(self, request, solution):
        test_results = solution.best_judgement.testcaseresult_set.all()

        if self.permissions.sample_results and not self.permissions.results:
            # Show only sample test cases
            test_results = test_results.filter(is_sample=True)

        context = self.get_context_data(test_results=test_results)
        return render(request, self.template_name, context)


class SolutionJudgementsView(BaseSolutionView):
    tab = 'judgements'
    template_name = 'solutions/solution_judgements.html'

    def is_allowed(self, permissions):
        return permissions.judgements

    def do_get(self, request, solution):
        judgements = solution.judgement_set.order_by('-id').select_related('extra_info').all()
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
                prefetch_related('compiler').\
                select_related('source_code', 'best_judgement').\
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
        if permissions.sample_results or permissions.results:
            if judgement is not None:
                test_results_count = judgement.testcaseresult_set.count()
                if test_results_count > 0:
                    return SolutionTestsView
                if judgement.outcome == Outcome.CHECK_FAILED:
                    return SolutionTestsView

        if permissions.compilation_log:
            if judgement is not None:
                return SolutionLogView

        if permissions.source_code:
            return SolutionSourceView

        if permissions.state_on_samples:
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
        return permissions.state_on_samples or permissions.state

    def do_get(self, request, solution):
        judgement = solution.best_judgement

        if judgement is not None:
            final = (judgement.status == Judgement.DONE)
            complete = self.permissions.state
            data = {
                'text': force_text(judgement.show_status(complete)),
                'final': final
            }
            if final:
                if complete or (judgement.sample_tests_passed is False):
                    data['color'] = 'green' if (judgement.outcome == Outcome.ACCEPTED) else 'red'
                else:
                    data['color'] = 'yellow'
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
        if permissions.tests_data:
            return True
        if permissions.sample_results:
            testcaseresult_id = self.kwargs.get('testcaseresult_id')
            if testcaseresult_id is not None:
                is_sample = TestCaseResult.objects.filter(pk=testcaseresult_id).values_list('is_sample', flat=True).first()
                if is_sample:
                    return True
        return False


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


class SolutionPlagiarismView(BaseSolutionView):
    tab = 'plagiarism'
    template_name = 'solutions/solution_plagiarism.html'
    paginate_by = 25

    def is_allowed(self, permissions):
        return permissions.plagiarism

    def do_get(self, request, solution):
        plagiarism_judgements = JudgementResult.\
            objects.filter(solution_to_judge=solution).all().\
            select_related('solution_to_compare').\
            select_related('solution_to_compare__author').\
            order_by('-similarity', '-solution_to_compare__reception_time')

        context = paginate(request, plagiarism_judgements, self.paginate_by)
        context = self.get_context_data(**context)
        return render(request, self.template_name, context)

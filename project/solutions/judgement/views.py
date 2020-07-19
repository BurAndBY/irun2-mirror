from collections import namedtuple

from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.views import generic

from cauth.mixins import ProblemEditorMemberRequiredMixin, StaffMemberRequiredMixin
from common.pagination import paginate
from problems.calcpermissions import get_problem_ids_queryset, has_limited_problems_queryset
from storage.storage import create_storage

from solutions.mixins import TestCaseResultMixin
from solutions.models import Solution, Judgement, TestCaseResult, JudgementLog
from solutions.permissions import SolutionPermissions
from solutions.solution.calcpermissions import calculate_permissions


class JudgementListView(ProblemEditorMemberRequiredMixin, generic.View):
    paginate_by = 25
    template_name = 'solutions/judgement_list.html'

    def get(self, request):
        queryset = Judgement.objects.prefetch_related('extra_info').order_by('-id')
        if has_limited_problems_queryset(request.user):
            queryset = queryset.filter(solution__problem_id__in=get_problem_ids_queryset(request.user))

        context = paginate(request, queryset, self.paginate_by, allow_all=True, show_total_count=request.user.is_staff)
        return render(request, self.template_name, context)


class JudgementMixin(ProblemEditorMemberRequiredMixin):
    def dispatch(self, request, judgement_id, *args, **kwargs):
        solution = Solution.objects.filter(judgement__id=judgement_id).first()
        if solution is None:
            raise Http404('Judjement not found')
        permissions, _ = calculate_permissions(solution, self.request.user)
        if not permissions.can_view_judgements:
            raise Http404('Access denied')
        return super().dispatch(request, judgement_id, *args, **kwargs)


class JudgementView(JudgementMixin, generic.View):
    template_name = 'solutions/judgement.html'

    def get(self, request, judgement_id):
        judgement = get_object_or_404(Judgement, pk=judgement_id)
        test_results = judgement.testcaseresult_set.all()

        storage = create_storage()
        logs = [storage.represent(log.resource_id) for log in JudgementLog.objects.filter(judgement_id=judgement.id)]

        permissions = SolutionPermissions().allow_all()

        return render(request, self.template_name, {
            'judgement': judgement,
            'logs': logs,
            'test_results': test_results,
            'solution_permissions': permissions,
            'extra_info': judgement.extra_info if hasattr(judgement, 'extra_info') else None,
        })


class JudgementStorageView(StaffMemberRequiredMixin, generic.View):
    template_name = 'solutions/judgement_storage.html'

    StorageInfo = namedtuple('StorageInfo', 'output stdout stderr')

    @staticmethod
    def aggregate_storage(storage, test_results):
        return JudgementStorageView.StorageInfo(
            sum((storage.get_size_on_disk(tr.output_resource_id) or 0) for tr in test_results),
            sum((storage.get_size_on_disk(tr.stdout_resource_id) or 0) for tr in test_results),
            sum((storage.get_size_on_disk(tr.stderr_resource_id) or 0) for tr in test_results),
        )

    def get(self, request, judgement_id):
        judgement = get_object_or_404(Judgement, pk=judgement_id)
        test_results = judgement.testcaseresult_set.all()

        storage = create_storage()
        return render(request, self.template_name, {
            'judgement': judgement,
            'storage': self.aggregate_storage(storage, test_results),
        })

    def post(self, request, judgement_id):
        TestCaseResult.objects.filter(judgement_id=judgement_id).update(
            output_resource_id=None,
            stdout_resource_id=None,
            stderr_resource_id=None,
        )
        return redirect('solutions:show_judgement', judgement_id)


class JudgementTestCaseResultView(JudgementMixin, TestCaseResultMixin, generic.View):
    template_name = 'solutions/testcaseresult.html'

    def get(self, request, judgement_id, testcaseresult_id):
        testcaseresult = get_object_or_404(TestCaseResult, judgement_id=judgement_id, id=testcaseresult_id)
        return self.serve_testcaseresult_page(testcaseresult, 'solutions:judgement_testdata', 'solutions:judgement_testimage', judgement_id, True)


class JudgementTestCaseResultDataView(JudgementMixin, TestCaseResultMixin, generic.View):
    def get(self, request, judgement_id, testcaseresult_id, mode):
        testcaseresult = get_object_or_404(TestCaseResult, judgement_id=judgement_id, id=testcaseresult_id)
        return self.serve_testcaseresult_data(mode, testcaseresult)


class JudgementTestCaseResultImageView(JudgementMixin, TestCaseResultMixin, generic.View):
    def get(self, request, judgement_id, testcaseresult_id, filename):
        testcaseresult = get_object_or_404(TestCaseResult, judgement_id=judgement_id, id=testcaseresult_id)
        return self.serve_testcaseresult_image(filename, testcaseresult)

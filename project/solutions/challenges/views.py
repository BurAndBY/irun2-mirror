from django.db.models import Count

from common.pagination.views import IRunnerListView
from cauth.mixins import ProblemEditorMemberRequiredMixin
from problems.calcpermissions import get_problem_ids_queryset, has_limited_problems_queryset

from solutions.models import Challenge

'''
Global challenges list
'''


class ChallengeListView(ProblemEditorMemberRequiredMixin, IRunnerListView):
    template_name = 'solutions/challenge_list.html'

    def get_queryset(self):
        qs = Challenge.objects.\
            annotate(num_solutions=Count('challengedsolution')).\
            select_related('problem').\
            order_by('-creation_time', '-id').\
            all()
        if has_limited_problems_queryset(self.request.user):
            qs = qs.filter(problem_id__in=get_problem_ids_queryset(self.request.user))
        return qs

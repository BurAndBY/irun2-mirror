from collections import namedtuple

from django.db.models import Count

from common.outcome import Outcome
from problems.models import Problem
from solutions.models import Judgement

ProblemInfo = namedtuple('ProblemInfo', 'all_solution_count accepted_solution_count test_count')


class ProblemInfoManager(object):
    @staticmethod
    def make_counts(queryset):
        result = {}
        for problem_id, count in queryset:
            result[problem_id] = count
        return result

    def __init__(self, problems):
        '''
        problems: queryset
        '''

        problem_ids = list(problems.values_list('pk', flat=True))
        problems = Problem.objects.filter(pk__in=problem_ids).order_by()

        qs = problems.\
            annotate(cnt=Count('solution')).\
            values_list('pk', 'cnt')
        self.all_solution_counts = ProblemInfoManager.make_counts(qs)

        qs = problems.\
            filter(solution__best_judgement__status=Judgement.DONE, solution__best_judgement__outcome=Outcome.ACCEPTED).\
            annotate(cnt=Count('solution')).\
            values_list('pk', 'cnt')
        self.accepted_solution_counts = ProblemInfoManager.make_counts(qs)

        qs = problems.\
            annotate(cnt=Count('testcase')).\
            values_list('pk', 'cnt')
        self.test_counts = ProblemInfoManager.make_counts(qs)

    def get(self, problem_id):
        return ProblemInfo(
            self.all_solution_counts.get(problem_id, 0),
            self.accepted_solution_counts.get(problem_id, 0),
            self.test_counts.get(problem_id, 0),
        )

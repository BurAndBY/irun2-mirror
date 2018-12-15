from collections import namedtuple

from problems.models import Problem, ProblemAccess
from solutions.permissions import SolutionAccessLevel

InProblemAccessLevel = namedtuple('InProblemAccessLevel', 'has_problem level')


def get_problems_queryset(user):
    if user is None or not user.is_authenticated:
        return Problem.objects.none()

    if not user.is_staff:
        return Problem.objects.filter(problemaccess__user=user)

    return Problem.objects.all()


def calculate_problem_solution_access_level(solution, user):
    if solution.problem_id is not None:
        if ProblemAccess.objects.filter(problem_id=solution.problem_id, user=user).exists():
            return InProblemAccessLevel(True, SolutionAccessLevel.FULL)

    return InProblemAccessLevel(False, SolutionAccessLevel.NO_ACCESS)

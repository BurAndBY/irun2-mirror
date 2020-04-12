from collections import namedtuple
from six.moves import reduce
import operator

from django.db.models import Q

from problems.models import Problem, ProblemAccess, ProblemFolder
from solutions.permissions import SolutionAccessLevel

InProblemAccessLevel = namedtuple('InProblemAccessLevel', 'has_problem level')


def _get_group_owned_problems(user):
    clauses = []
    for tree_id, lft, rght in ProblemFolder.objects.\
            filter(problemfolderaccess__group__users=user).\
            values_list('tree_id', 'lft', 'rght'):
        clauses.append(Q(folders__tree_id=tree_id) & Q(folders__lft__gte=lft) & Q(folders__lft__lte=rght))
    if not clauses:
        return Problem.objects.none()
    return Problem.objects.filter(reduce(operator.or_, clauses))


def _get_personally_shared_problems(user):
    return Problem.objects.filter(problemaccess__user=user)


def has_limited_problems_queryset(user):
    return not (user.is_authenticated and user.is_staff)


def get_problems_queryset(user):
    if user is None or not user.is_authenticated:
        return Problem.objects.none()

    if user.is_staff:
        return Problem.objects.all()

    return _get_personally_shared_problems(user) | _get_group_owned_problems(user)


def get_problem_ids_queryset(user):
    return get_problems_queryset(user).values_list('id')


def calculate_problem_solution_access_level(solution, user):
    if solution.problem_id is not None:
        if ProblemAccess.objects.filter(problem_id=solution.problem_id, user=user).exists():
            return InProblemAccessLevel(True, SolutionAccessLevel.FULL)

    return InProblemAccessLevel(False, SolutionAccessLevel.NO_ACCESS)

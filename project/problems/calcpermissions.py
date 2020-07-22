from collections import namedtuple
from six.moves import reduce
import operator

from django.db.models import Q

from problems.models import Problem, ProblemFolder
from problems.problem.permissions import ProblemPermissionCalcer
from solutions.permissions import SolutionAccessLevel, SolutionPermissions


InProblemAccessPermissions = namedtuple('InProblemAccessLevel', 'has_problem permissions')


def _get_group_owned_problems(user):
    clauses = []
    if user.is_admin:
        for tree_id, lft, rght in ProblemFolder.objects.\
                filter(problemfolderaccess__group__users=user).\
                values_list('tree_id', 'lft', 'rght').\
                order_by():
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

    return _get_personally_shared_problems(user).order_by().union(_get_group_owned_problems(user).order_by())


def get_problem_ids_queryset(user):
    return set(get_problems_queryset(user).values_list('id', flat=True))


def calculate_problem_solution_permissions(solution, user):
    permissions = SolutionPermissions()

    if solution.problem_id is not None:
        pp = ProblemPermissionCalcer(user).calc(solution.problem_id)
        if pp is not None:
            permissions.update(SolutionAccessLevel.FULL)
            permissions.allow_refer_to_problem()
            permissions.allow_view_plagiarism_score()
            permissions.allow_view_plagiarism_details()
            permissions.allow_view_judgements()

            if pp.can_rejudge:
                permissions.allow_rejudge()

    return permissions

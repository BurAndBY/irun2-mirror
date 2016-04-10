from solutions.permissions import SolutionAccessLevel

from .models import Contest, Membership, UnauthorizedAccessLevel
from .permissions import ContestPermissions, InContestAccessLevel


def calculate_contest_permissions(contest, user, memberships):
    '''
    Memberships should refer the same user and the given contest.
    '''
    permissions = ContestPermissions()
    if contest.unauthorized_access != UnauthorizedAccessLevel.NO_ACCESS:
        permissions.standings = True
        if contest.unauthorized_access == UnauthorizedAccessLevel.VIEW_STANDINGS_AND_PROBLEMS:
            permissions.problems = True

    if user is not None:
        if user.is_staff:
            permissions.set_admin()

        for membership in memberships:
            assert membership.user_id == user.id
            assert membership.contest_id == contest.id

            if membership.role == Membership.CONTESTANT:
                permissions.set_contestant(contest.contestant_own_solutions_access)
            elif membership.role == Membership.JUROR:
                permissions.set_juror()

    return permissions


def calculate_contest_solution_access_level(solution, user):
    level = SolutionAccessLevel.NO_ACCESS

    contest = Contest.objects.\
        filter(contestsolution__solution_id=solution.id).\
        first()

    if contest is None:
        # the solution does not belong to any contest
        return InContestAccessLevel(None, level)

    for role in Membership.objects.filter(contest=contest, user=user).values_list('role', flat=True):
        if role == Membership.CONTESTANT:
            if solution.author_id == user.id:
                level = max(level, contest.contestant_own_solutions_access)
        elif role == Membership.JUROR:
            level = max(level, SolutionAccessLevel.FULL)
    # level remains NO_ACCESS if user is not a member of the contest

    return InContestAccessLevel(contest, level)

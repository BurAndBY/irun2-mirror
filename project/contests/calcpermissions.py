from solutions.permissions import SolutionAccessLevel

from .models import Contest, Membership, UnauthorizedAccessLevel
from .permissions import ContestPermissions, InContestAccessLevel
from .services import ContestTiming, create_contest_service


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
    samples_only_state = True

    contest = Contest.objects.\
        filter(contestsolution__solution_id=solution.id).\
        first()

    if contest is None:
        # the solution does not belong to any contest
        return InContestAccessLevel(None, level, samples_only_state)

    timing = ContestTiming(contest)
    service = create_contest_service(contest)

    for role in Membership.objects.filter(contest=contest, user=user).values_list('role', flat=True):
        if role == Membership.CONTESTANT:
            if solution.author_id == user.id:
                level = max(level, contest.contestant_own_solutions_access)
                if service.should_show_my_solutions_completely(timing):
                    samples_only_state = False

        elif role == Membership.JUROR:
            level = max(level, SolutionAccessLevel.FULL)
            samples_only_state = False
    # level remains NO_ACCESS if user is not a member of the contest

    return InContestAccessLevel(contest, level, samples_only_state)

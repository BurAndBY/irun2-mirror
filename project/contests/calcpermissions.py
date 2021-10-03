from solutions.permissions import SolutionAccessLevel, SolutionPermissions

from .models import Contest, Membership, UnauthorizedAccessLevel
from .permissions import ContestPermissions, InContestAccessPermissions
from .services import ContestTiming, create_contest_service


class ContestMemberFlags(object):
    def __init__(self):
        # Both flags may be true
        self.is_contestant = False
        self.is_juror = False
        self.is_admin = False

    def __bool__(self):
        return self.is_contestant or self.is_juror or self.is_admin

    @staticmethod
    def load(contest, user):
        flags = ContestMemberFlags()

        if user.is_authenticated:
            for role in Membership.objects.filter(contest=contest, user=user).values_list('role', flat=True):
                if role == Membership.CONTESTANT:
                    flags.is_contestant = True
                elif role == Membership.JUROR:
                    flags.is_juror = True

            # if is_instance_owned(contest, user):
            #    flags.is_admin = True
            if user.is_staff:
                flags.is_admin = True

        return flags


def calculate_contest_permissions(contest, member_flags):
    '''
    Memberships should refer the same user and the given contest.
    '''
    permissions = ContestPermissions()
    if contest.unauthorized_access != UnauthorizedAccessLevel.NO_ACCESS:
        permissions.standings = True
        if contest.unauthorized_access == UnauthorizedAccessLevel.VIEW_STANDINGS_AND_PROBLEMS:
            permissions.problems = True

    if member_flags.is_admin:
        permissions.set_admin()
    if member_flags.is_contestant:
        permissions.set_contestant(contest.contestant_own_solutions_access)
    if member_flags.is_juror:
        permissions.set_juror()

    if not contest.enable_printing:
        permissions.disable_printing()

    return permissions


def calculate_contest_solution_permissions_ex(solution, user):
    permissions = SolutionPermissions()

    contest = Contest.objects.filter(contestsolution__solution_id=solution.id).first()
    if contest is None:
        # the solution does not belong to any contest
        return InContestAccessPermissions(None, False, permissions)

    timing = ContestTiming(contest)
    service = create_contest_service(contest)
    member_flags = ContestMemberFlags.load(contest, user)

    if member_flags.is_contestant and solution.author_id == user.id:
        cp = SolutionPermissions()
        cp.update(contest.contestant_own_solutions_access)
        if not service.should_show_my_solutions_completely(timing):
            cp.deny_view_state()
        permissions |= cp

    if member_flags.is_juror or member_flags.is_admin:
        cp = SolutionPermissions()
        cp.update(SolutionAccessLevel.FULL)
        cp.allow_view_ip_address()
        permissions |= cp

    # `permissions` remains default-constructed if user is not a member of the contest

    return InContestAccessPermissions(contest, bool(member_flags), permissions)

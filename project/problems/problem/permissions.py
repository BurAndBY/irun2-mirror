from common.access import Permissions
from common.accessmode import AccessMode

from problems.models import ProblemAccess


class SingleProblemPermissions(Permissions):
    EDIT = 1 << 0
    REJUDGE = 1 << 1
    CHALLENGE = 1 << 2
    MOVE = 1 << 3
    DELETE = 1 << 4
    ALL = EDIT | REJUDGE | CHALLENGE | MOVE | DELETE


def calc_problem_permissions(user, problem_id):
    if not user.is_authenticated:
        return None
    if user.is_staff:
        return SingleProblemPermissions.all()

    access = ProblemAccess.objects.filter(problem_id=problem_id, user=user).first()
    if access is not None:
        if access.mode == AccessMode.READ:
            return SingleProblemPermissions()
        elif access.mode == AccessMode.WRITE:
            return SingleProblemPermissions(SingleProblemPermissions.EDIT | SingleProblemPermissions.CHALLENGE | SingleProblemPermissions.REJUDGE)


def calc_problems_permissions(user, problem_ids):
    return {problem_id: calc_problem_permissions(user, problem_id) for problem_id in set(problem_ids)}

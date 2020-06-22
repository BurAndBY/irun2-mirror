from common.access import Permissions
from cauth.acl.accessmode import AccessMode
from cauth.acl.checker import FolderAccessChecker

from problems.models import ProblemAccess, ProblemFolder, ProblemFolderAccess


class _ProblemFolderAccessChecker(FolderAccessChecker):
    folder_model = ProblemFolder
    folder_access_model = ProblemFolderAccess
    folder_model_object_field = 'problem__id'


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

    # group access
    res_mode = _ProblemFolderAccessChecker.check(user, problem_id)
    # individual access
    if res_mode != AccessMode.WRITE:
        for mode in ProblemAccess.objects.filter(problem_id=problem_id, user=user).values_list('mode', flat=True):
            res_mode = max(res_mode, mode)

    if res_mode == AccessMode.READ:
        return SingleProblemPermissions()
    elif res_mode == AccessMode.WRITE:
        return SingleProblemPermissions(SingleProblemPermissions.EDIT | SingleProblemPermissions.CHALLENGE | SingleProblemPermissions.REJUDGE)


def calc_problems_permissions(user, problem_ids):
    return {problem_id: calc_problem_permissions(user, problem_id) for problem_id in set(problem_ids)}

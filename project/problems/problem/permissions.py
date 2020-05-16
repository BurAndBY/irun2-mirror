from common.access import Permissions
from cauth.acl.accessmode import AccessMode
from cauth.acl.checker import FolderAccessChecker

from problems.models import ProblemAccess, ProblemFolder, ProblemFolderAccess


class ProblemFolderAccessChecker(FolderAccessChecker):
    folder_model = ProblemFolder
    folder_access_model = ProblemFolderAccess
    folder_model_object_field = 'problem'


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

    res_mode = 0
    for mode in ProblemAccess.objects.filter(problem_id=problem_id, user=user).values_list('mode', flat=True):
        res_mode = max(res_mode, mode)

    res_mode = max(res_mode, ProblemFolderAccessChecker.check(user, problem_id))

    if res_mode == AccessMode.READ:
        return SingleProblemPermissions()
    elif res_mode == AccessMode.WRITE:
        return SingleProblemPermissions(SingleProblemPermissions.EDIT | SingleProblemPermissions.CHALLENGE | SingleProblemPermissions.REJUDGE)


def calc_problems_permissions(user, problem_ids):
    return {problem_id: calc_problem_permissions(user, problem_id) for problem_id in set(problem_ids)}

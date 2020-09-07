from common.access import Permissions, PermissionCalcer
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


class ProblemPermissionCalcer(PermissionCalcer):
    permissions_cls = SingleProblemPermissions

    def _do_fill_permission_map(self, pm):
        read = SingleProblemPermissions()
        write = SingleProblemPermissions().allow_edit().allow_challenge().allow_rejudge()

        if getattr(self.user, 'is_admin', True):
            # group access
            pks = pm.find_pks_for_granting(write)
            if pks:
                for pk, mode in _ProblemFolderAccessChecker.bulk_check(self.user, pks).items():
                    if mode in (AccessMode.MODIFY, AccessMode.WRITE):
                        pm.grant(pk, write)
                    elif mode == AccessMode.READ:
                        pm.grant(pk, read)

        if getattr(self.user, 'is_problem_editor', True):
            # individual access
            pks = pm.find_pks_for_granting(write)
            if pks:
                for pk, mode in ProblemAccess.objects.filter(user=self.user, problem_id__in=pks).values_list('problem_id', 'mode'):
                    if mode in (AccessMode.MODIFY, AccessMode.WRITE):
                        pm.grant(pk, write)
                    elif mode == AccessMode.READ:
                        pm.grant(pk, read)

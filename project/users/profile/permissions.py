import operator
from six.moves import reduce

from django.contrib import auth
from django.db.models import Q

from cauth.acl.accessmode import AccessMode
from cauth.acl.checker import FolderAccessChecker
from common.access import Permissions, PermissionCalcer

from users.models import AdminGroup, UserFolder, UserFolderAccess


class ProfilePermissions(Permissions):
    EDIT = 1 << 0
    JOIN_TO_STAFF = 1 << 1


class _UserFolderAccessChecker(FolderAccessChecker):
    folder_model = UserFolder
    folder_access_model = UserFolderAccess
    folder_model_object_field = 'userprofile__user_id'


def _list_my_admin_group_user_ids(user):
    # produces single SQL query
    my_groups = AdminGroup.objects.filter(users=user)
    return set(user_id for user_id, in AdminGroup.objects.filter(id__in=my_groups).values_list('users__id'))


class ProfilePermissionCalcer(PermissionCalcer):
    permissions_cls = ProfilePermissions

    def _do_fill_permission_map(self, pm):
        if self.user.is_admin:
            pm.grant(self.user.id, ProfilePermissions.allow_edit())

            pks = pm.find_pks_for_granting(ProfilePermissions.allow_edit())
            if pks:
                for pk, mode in _UserFolderAccessChecker.bulk_check(self.user, pks).items():
                    if mode == AccessMode.WRITE:
                        pm.grant(pk, ProfilePermissions.allow_edit())
                    elif mode == AccessMode.READ:
                        pm.grant(pk, ProfilePermissions.basic())

            pks = pm.find_pks_for_granting(ProfilePermissions.basic())
            if pks:
                for user_id in _list_my_admin_group_user_ids(self.user):
                    pm.grant(user_id, ProfilePermissions.basic())


def get_user_queryset(user):
    qs = auth.get_user_model().objects

    if user.is_staff:
        return qs.all()

    if user.is_admin:
        clauses = [
            Q(id__in=_list_my_admin_group_user_ids(user))
        ]
        for tree_id, lft, rght in UserFolder.objects.\
                filter(userfolderaccess__group__users=user).\
                values_list('tree_id', 'lft', 'rght').\
                order_by():
            clauses.append(
                Q(userprofile__folder__tree_id=tree_id) &
                Q(userprofile__folder__lft__gte=lft) &
                Q(userprofile__folder__lft__lte=rght)
            )
        if clauses:
            return qs.filter(reduce(operator.or_, clauses))

    return qs.none()

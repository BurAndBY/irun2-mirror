from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model

from common.tree.loader import FolderLoader

from users.models import UserFolder, UserFolderAccess


class UserFolderLoader(FolderLoader):
    root_name = _('Users')
    model = get_user_model()
    folder_model = UserFolder
    folder_access_model = UserFolderAccess

    @classmethod
    def get_folder_content(cls, user, node):
        qs = get_user_model().objects.filter(userprofile__folder_id=node.id)
        if node.access == 0:
            # partial access
            qs = qs.filter(admingroup__in=UserFolderLoader._my_admin_groups(user))
        return qs

    @staticmethod
    def _my_admin_groups(user):
        if user.is_staff:
            return set()
        if user.is_admin:
            return user.admingroup_ids
        return set()

    @classmethod
    def get_extra_objects(cls, user):
        return get_user_model().objects.filter(admingroup__in=UserFolderLoader._my_admin_groups(user))

    @classmethod
    def get_extra_folders(cls, user):
        return UserFolder.objects.filter(userprofile__user__admingroup__in=UserFolderLoader._my_admin_groups(user))

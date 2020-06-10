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
            qs = qs.filter(id=user.id)
        return qs

    @classmethod
    def get_extra_object_pks(cls, user):
        return [user.id]

    @classmethod
    def get_extra_folders(cls, user):
        return UserFolder.objects.filter(userprofile__user=user)

from common.access import PermissionCheckMixin

from users.profile.permissions import ProfilePermissions


class ProfilePermissionCheckMixin(PermissionCheckMixin):
    def _make_permissions(self, user):
        if not user.is_authenticated:
            return None
        if user.is_staff:
            return ProfilePermissions.all()
        return None

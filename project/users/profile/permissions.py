from common.access import Permissions


class ProfilePermissions(Permissions):
    EDIT = 1 << 0
    JOIN_TO_STAFF = 1 << 1

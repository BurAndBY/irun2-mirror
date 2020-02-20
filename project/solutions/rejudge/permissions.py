from common.access import Permissions


class RejudgePermissions(Permissions):
    CLONE = 1 << 0
    COMMIT = 1 << 1

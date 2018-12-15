from common.access import Permissions


class SingleProblemPermissions(Permissions):
    EDIT = 1 << 0
    REJUDGE = 1 << 1
    CHALLENGE = 1 << 2
    MOVE = 1 << 3
    DELETE = 1 << 4
    ALL = EDIT | REJUDGE | CHALLENGE | MOVE | DELETE

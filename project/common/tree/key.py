ROOT = 'root'


class FolderId(object):
    @staticmethod
    def to_string(value):
        return str(value) if value is not None else ROOT

    @staticmethod
    def from_string(value):
        return None if value == ROOT else int(value)

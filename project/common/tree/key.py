from django.http import Http404

ROOT = 'root'


class FolderId(object):
    @staticmethod
    def to_string(value):
        return str(value) if value is not None else ROOT

    @staticmethod
    def from_string(value):
        return None if value == ROOT else int(value)


def folder_id_or_404(value):
    try:
        return FolderId.from_string(value)
    except ValueError:
        raise Http404('invalid folder id')

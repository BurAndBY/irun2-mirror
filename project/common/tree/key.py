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


class FolderIdConverter(object):
    regex = r'\d+|%s' % (ROOT,)

    def to_python(self, value):
        return FolderId.from_string(value)

    def to_url(self, value):
        return FolderId.to_string(value)

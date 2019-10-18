from __future__ import unicode_literals

import six
import zipfile

from django.http import HttpResponse

from storage.storage import create_storage


class ZipSaver(object):
    def __init__(self, name):
        self._zip_file_name = name
        self._zip_blob = b''

    def writer(self):
        return ZipWriter(self)

    def serve(self):
        # Grab ZIP file from in-memory, make response with correct MIME-type
        response = HttpResponse(self._zip_blob, content_type='application/x-zip-compressed')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(self._zip_file_name)
        return response


class ZipWriter(object):
    def __init__(self, parent):
        self._parent = parent

        # Open StringIO to grab in-memory ZIP contents
        self._stream = six.StringIO()
        self._zipfile = zipfile.ZipFile(self._stream, 'w', zipfile.ZIP_DEFLATED)
        self._storage = create_storage()

    def add(self, resource_id, name_in_archive, max_size):
        if resource_id is None:
            return

        blob, is_complete = self._storage.read_blob(resource_id, max_size=max_size)
        if is_complete:
            self._zipfile.writestr(name_in_archive, blob)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._zipfile.close()
        self._parent._zip_blob = self._stream.getvalue()
        return False

from django import forms
from django.core.files.uploadedfile import UploadedFile

from storage.models import FileMetadata
from storage.utils import store_with_metadata


class _FakeFile(object):
    def __init__(self, url, name):
        self.url = url
        self.name = name

    def __str__(self):
        return self.name


class FileMetadataField(forms.FileField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.urlmaker = None

    @staticmethod
    def _is_pk(value):
        return isinstance(value, int)

    def clean(self, data, initial=None):
        data = super().clean(data, initial=initial)
        if data is False:
            return None
        if isinstance(data, UploadedFile):
            return store_with_metadata(data)
        if self._is_pk(data):
            return FileMetadata.objects.get(pk=data)

    def prepare_value(self, value):
        if self._is_pk(value):
            filemetadata = FileMetadata.objects.get(pk=value)
            return _FakeFile(self.urlmaker(filemetadata), filemetadata.filename)

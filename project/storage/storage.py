import binascii
import hashlib
import os
import tempfile

from django.core.files.base import File
from django.core.servers.basehttp import FileWrapper
from django.db import models

HASH_SIZE = 20


class ResourceId(object):
    def __init__(self, binary=''):
        if not isinstance(binary, str):
            raise TypeError('Binary string expected, {0} found'.format(type(binary)))
        if len(binary) > HASH_SIZE:
            raise ValueError('Resource id must have length not greater than {0}'.format(HASH_SIZE))
        self._binary = binary

    def get_binary(self):
        return self._binary

    def __str__(self):
        return binascii.b2a_hex(self._binary)

    @staticmethod
    def parse(s):
        return ResourceId(binascii.a2b_hex(s))

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and self._binary == other._binary)

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_representation(self, obj):
        return str(obj)


class ResourceIdField(models.BinaryField):
    description = "Data storage resource identifier"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 20
        super(ResourceIdField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(ResourceIdField, self).deconstruct()
        del kwargs['max_length']
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value

        return ResourceId(str(value))

    def to_python(self, value):
        if isinstance(value, ResourceId):
            return value

        if value is None:
            return value

        return ResourceId(str(value))

    def get_prep_value(self, value):
        if isinstance(value, ResourceId):
            value = value.get_binary()

        return super(ResourceIdField, self).get_prep_value(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        if isinstance(value, ResourceId):
            value = value.get_binary()

        return super(ResourceIdField, self).get_db_prep_value(value, connection, prepared)


def _get_data_directly(resource_id):
    blob = resource_id.get_binary()
    return blob if len(blob) < HASH_SIZE else None


class ResourseRepresentation(object):
    IS_BINARY = 1
    IS_COMPLETE = 2
    IS_UTF8 = 4
    HAS_BOM = 8

    def __init__(self, size, flags, text):
        self.size = size
        self.flags = flags
        self.text = text

    def is_binary(self):
        return bool(ResourseRepresentation.IS_BINARY & self.flags)

    def is_complete(self):
        return bool(ResourseRepresentation.IS_COMPLETE & self.flags)

    def is_utf8(self):
        return bool(ResourseRepresentation.IS_UTF8 & self.flags)

    def has_bom(self):
        return bool(ResourseRepresentation.HAS_BOM & self.flags)

    def is_empty(self):
        return self.size == 0

    @property
    def complete_text(self):
        return self.text if self.is_complete() else None


class ServedData(object):
    def __init__(self, size, generator):
        self.size = size
        self.generator = generator


def _is_binary(blob):
    for ch in blob:
        code = ord(ch)
        if not ((9 <= code <= 13) or (32 <= code <= 126) or (128 <= code <= 255)):
            return True
    return False


def _cut_utf8_bom(blob):
    return blob[3:] if blob.startswith('\xEF\xBB\xBF') else None


def _try_decode_utf8(blob, is_complete):
    try:
        return blob.decode('utf-8')
    except UnicodeDecodeError:
        pass

    if not is_complete:
        # try to cut the last char: it may be broken
        try:
            return blob[:-1].decode('utf-8')
        except UnicodeDecodeError:
            pass

    return None


def _try_decode_ascii(blob):
    try:
        return blob.decode('windows-1251')
    except UnicodeDecodeError:
        pass

    return None


def _represent(blob, full_size):
    assert len(blob) <= full_size
    is_complete = len(blob) == full_size

    flags = 0
    text = None

    if is_complete:
        flags |= ResourseRepresentation.IS_COMPLETE

    if _is_binary(blob):
        flags |= ResourseRepresentation.IS_BINARY
    else:
        no_bom_blob = _cut_utf8_bom(blob)
        if no_bom_blob is not None:
            text = _try_decode_utf8(no_bom_blob, is_complete)
            if text is not None:
                flags |= ResourseRepresentation.IS_UTF8
                flags |= ResourseRepresentation.HAS_BOM
        else:
            text = _try_decode_utf8(blob, is_complete)
            if text is not None:
                flags |= ResourseRepresentation.IS_UTF8

        if text is None:
            text = _try_decode_ascii(blob)

    return ResourseRepresentation(full_size, flags, text)


def _serve_string(s):
    return ServedData(len(s), (s,))

DEFAULT_REPRESENTATION_LIMIT = 2**16


class IDataStorage(object):
    def save(self, f):
        raise NotImplementedError()

    def represent(self, resource_id, limit=DEFAULT_REPRESENTATION_LIMIT):
        raise NotImplementedError()

    def serve(self, resource_id):
        raise NotImplementedError()

    def check_availability(self, resource_ids):
        raise NotImplementedError()

    def list_all(self):
        '''
        Generates tuples (resource_id, size) for each stored file.
        Slow, used for debugging only.
        '''
        raise NotImplementedError()


class FileSystemStorage(IDataStorage):
    def __init__(self, directory):
        self._directory = directory
        if not os.path.exists(directory):
            os.mkdir(directory)

            for subdir in FileSystemStorage._list_subdirectory_names(directory):
                if not os.path.exists(subdir):
                    os.mkdir(subdir)

    @staticmethod
    def _list_subdirectory_names(directory):
        for x in range(256):
            subdir = os.path.join(directory, binascii.b2a_hex(chr(x)))
            yield subdir

    def _get_path(self, resource_id):
        s = str(resource_id)
        assert len(s) == HASH_SIZE * 2
        return os.path.join(self._directory, s[:2], s)

    def _get_temp_file(self):
        return tempfile.NamedTemporaryFile(dir=self._directory, delete=False)

    def _do_save(self, f):
        h = hashlib.sha1()
        for chunk in f.chunks():
            h.update(chunk)

        resource_id = ResourceId(h.digest())

        target_name = self._get_path(resource_id)

        if not os.path.exists(target_name):
            with self._get_temp_file() as fd:
                for chunk in f.chunks():
                    fd.write(chunk)
                temp_name = fd.name

            if not os.path.exists(target_name):
                try:
                    os.rename(temp_name, target_name)
                except WindowsError:
                    pass
            else:
                os.remove(temp_name)

        return resource_id

    def save(self, f):
        if not isinstance(f, File):
            raise TypeError('File expected')

        if f.size < HASH_SIZE:
            # do not write anything to disk
            data = f.read()
            return ResourceId(data)
        else:
            return self._do_save(f)

    def represent(self, resource_id, limit=DEFAULT_REPRESENTATION_LIMIT):
        if resource_id is None:
            return None
        blob = _get_data_directly(resource_id)
        if blob is not None:
            return _represent(blob, len(blob))

        target_name = self._get_path(resource_id)
        if not os.path.exists(target_name):
            return None

        with open(target_name, 'rb') as fd:
            fd.seek(0, os.SEEK_END)
            size = fd.tell()

            part = size if size <= limit else limit

            fd.seek(0, os.SEEK_SET)
            blob = fd.read(part)
            return _represent(blob, size)

    def _is_exist(self, resource_id):
        blob = _get_data_directly(resource_id)
        if blob is not None:
            return True

        target_name = self._get_path(resource_id)
        if os.path.exists(target_name):
            return True

        return False

    def serve(self, resource_id):
        blob = _get_data_directly(resource_id)
        if blob is not None:
            return _serve_string(blob)

        target_name = self._get_path(resource_id)
        if not os.path.exists(target_name):
            return None

        fd = open(target_name, 'rb')
        fd.seek(0, os.SEEK_END)
        size = fd.tell()
        fd.seek(0, os.SEEK_SET)

        return ServedData(size, FileWrapper(fd))

    def check_availability(self, resource_ids):
        return [self._is_exist(resource_id) for resource_id in resource_ids]

    def list_all(self):
        for subdir in FileSystemStorage._list_subdirectory_names(self._directory):
            assert os.path.isdir(subdir)
            for filename in os.listdir(subdir):
                path = os.path.join(subdir, filename)
                yield (ResourceId.parse(filename), os.path.getsize(path))


def create_storage():
    return FileSystemStorage('c:\\temp\\out2')

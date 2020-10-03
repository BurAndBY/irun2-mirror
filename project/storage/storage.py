# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import binascii
import hashlib
import os
import six
import sys
import tempfile

from wsgiref.util import FileWrapper

from django.conf import settings
from django.core.files.base import File
from django.db import models
from django.utils.encoding import force_text

from .representation import represent_blob

HASH_SIZE = 20


class ResourceId(object):
    def __init__(self, binary=b''):
        if not isinstance(binary, six.binary_type):
            raise TypeError('Binary string expected, {0} found'.format(type(binary)))
        if len(binary) > HASH_SIZE:
            raise ValueError('Resource id must have length not greater than {0}'.format(HASH_SIZE))
        self._binary = binary

    def get_binary(self):
        return self._binary

    def __str__(self):
        return force_text(binascii.b2a_hex(self._binary), encoding='ascii')

    @staticmethod
    def parse(s):
        return ResourceId(binascii.a2b_hex(s))

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and self._binary == other._binary)

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_representation(self, obj):
        return force_text(obj)

    def __hash__(self):
        return hash(self._binary)

    def __len__(self):
        return len(self._binary)


class ResourceIdField(models.BinaryField):
    description = "Data storage resource identifier"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = HASH_SIZE
        super(ResourceIdField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(ResourceIdField, self).deconstruct()
        del kwargs['max_length']
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value

        return ResourceId(six.binary_type(value))

    def to_python(self, value):
        if isinstance(value, ResourceId):
            return value

        if value is None:
            return value

        return ResourceId(six.binary_type(value))

    def get_prep_value(self, value):
        if isinstance(value, ResourceId):
            value = value.get_binary()

        return super(ResourceIdField, self).get_prep_value(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        if isinstance(value, ResourceId):
            value = value.get_binary()

        return super(ResourceIdField, self).get_db_prep_value(value, connection, prepared)

    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return 'VARBINARY({})'.format(HASH_SIZE)
        else:
            return super().db_type(connection)


# Fake class to force migration
class ResourceIdFieldDeprecated(ResourceIdField):
    def db_type(self, connection):
        # Uses 'LONGBLOB' in MySQL by default
        return models.BinaryField.db_type(self, connection)


def _get_data_directly(resource_id):
    blob = resource_id.get_binary()
    return blob if len(blob) < HASH_SIZE else None


class ServedData(object):
    def __init__(self, size, generator):
        self.size = size
        self.generator = generator


def _serve_string(s):
    return ServedData(len(s), (s,))


DEFAULT_REPRESENTATION_LIMIT = 2**16


class IDataStorage(object):
    def save(self, f):
        raise NotImplementedError()

    def represent(self, resource_id, limit=DEFAULT_REPRESENTATION_LIMIT):
        raise NotImplementedError()

    def get_size_on_disk(self, resource_id):
        '''
        Returns file size (incl. storage overhead) or None if the file is not available.
        '''
        raise NotImplementedError()

    def serve(self, resource_id):
        raise NotImplementedError()

    def check_availability(self, resource_ids):
        raise NotImplementedError()

    def read_blob(self, resource_id, max_size):
        '''
        Returns a tuple (blob, is_complete).
        If file is larger than max_size, only max_size bytes are read.
        Returns (None, false) if file does not exist.
        '''
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
            subdir = os.path.join(directory, force_text(binascii.b2a_hex(six.int2byte(x))))
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
                except OSError as e:
                    # HACK: The file is locked by antivirus
                    if not (sys.platform.startswith('win') and isinstance(e, WindowsError)):
                        raise
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

    def represent(self, resource_id, limit=DEFAULT_REPRESENTATION_LIMIT, max_lines=None, max_line_length=None):
        if resource_id is None:
            return None
        blob = _get_data_directly(resource_id)
        if blob is not None:
            return represent_blob(blob, len(blob), max_lines, max_line_length)

        target_name = self._get_path(resource_id)
        if not os.path.exists(target_name):
            return None

        with open(target_name, 'rb') as fd:
            fd.seek(0, os.SEEK_END)
            size = fd.tell()

            part = size if size <= limit else limit

            fd.seek(0, os.SEEK_SET)
            blob = fd.read(part)
            return represent_blob(blob, size, max_lines, max_line_length)

    def get_size_on_disk(self, resource_id):
        if resource_id is None:
            return None
        blob = _get_data_directly(resource_id)
        if blob is not None:
            return 0

        target_name = self._get_path(resource_id)
        if not os.path.exists(target_name):
            return None

        # TODO
        BLOCK = 4096
        res = os.path.getsize(target_name)
        return (res + BLOCK - 1) // BLOCK * BLOCK

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

    def read_blob(self, resource_id, max_size):
        blob = _get_data_directly(resource_id)
        if blob is not None:
            if max_size is None or len(blob) <= max_size:
                return (blob, True)
            else:
                return (blob[:max_size], False)

        target_name = self._get_path(resource_id)
        if not os.path.exists(target_name):
            return (None, False)

        fd = open(target_name, 'rb')
        if max_size is None:
            return (fd.read(), True)
        else:
            blob = fd.read(max_size + 1)
            if len(blob) <= max_size:
                return (blob, True)
            else:
                return (blob[:max_size], False)

    def check_availability(self, resource_ids):
        return [self._is_exist(resource_id) for resource_id in resource_ids]

    def list_all(self):
        for subdir in FileSystemStorage._list_subdirectory_names(self._directory):
            assert os.path.isdir(subdir)
            for filename in os.listdir(subdir):
                path = os.path.join(subdir, filename)
                yield (ResourceId.parse(filename), os.path.getsize(path))


def create_storage():
    return FileSystemStorage(settings.STORAGE_DIR)

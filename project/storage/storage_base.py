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
from .resource_id import HASH_SIZE
from .resource_id import ResourceId


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
        '''
        Saves the given Django file and returns its resource_id.
        '''
        raise NotImplementedError()

    def represent(self, resource_id, limit=DEFAULT_REPRESENTATION_LIMIT, max_lines=None, max_line_length=None):
        '''
        Returns a ResourseRepresentation object or None if the file is missing.
        '''
        raise NotImplementedError()

    def get_size_on_disk(self, resource_id):
        '''
        Returns file size (incl. storage overhead) or None if the file is not available.
        '''
        raise NotImplementedError()

    def serve(self, resource_id):
        '''
        Returns ServedData object or None.
        '''
        raise NotImplementedError()

    def check_availability(self, resource_ids):
        '''
        Returns a list of boolean flags for each resource.
        '''
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


class DataStorage(IDataStorage):
    def _do_save(self, resource_id, f):
        # Saves a Django file and returns nothing
        raise NotImplementedError()

    def save(self, f):
        if not isinstance(f, File):
            raise TypeError('File expected')

        if f.size < HASH_SIZE:
            # do not write anything to disk
            data = f.read()
            resource_id = ResourceId(data)
        else:
            h = hashlib.sha1()
            for chunk in f.chunks():
                h.update(chunk)

            resource_id = ResourceId(h.digest())
            self._do_save(resource_id, f)
        return resource_id

    def represent(self, resource_id, limit=DEFAULT_REPRESENTATION_LIMIT, max_lines=None, max_line_length=None):
        if resource_id is None:
            return None
        blob, size = self.read_with_size(resource_id, limit)
        if blob is None:
            return None
        return represent_blob(blob, size, max_lines, max_line_length)

    def _do_get_size_on_disk(self, resource_id):
        # Must return actual_size or 0 if the file is absent
        raise NotImplementedError()

    def get_size_on_disk(self, resource_id):
        if resource_id is None:
            return 0
        blob = _get_data_directly(resource_id)
        if blob is not None:
            return 0
        return self._do_get_size_on_disk(resource_id)

    def _do_serve(self, resource_id):
        raise NotImplementedError()

    def serve(self, resource_id):
        blob = _get_data_directly(resource_id)
        if blob is not None:
            return _serve_string(blob)
        return self._do_serve(resource_id)

    def _do_read_with_size(self, resource_id, limit):
        # Returns (blob, full_size)
        raise NotImplementedError()

    def read_with_size(self, resource_id, max_size):
        blob = _get_data_directly(resource_id)
        if blob is not None:
            return (blob if max_size is None else blob[:max_size], len(blob))
        return self._do_read_with_size(resource_id, max_size)

    def read_blob(self, resource_id, max_size):
        blob, size = self.read_with_size(resource_id, max_size)
        if blob is not None:
            return (blob, size <= max_size if max_size is not None else True)
        return (None, False)

    def _do_get_existing_files(self, resource_ids):
        # returns a set of resource_ids
        raise NotImplementedError()

    def check_availability(self, resource_ids):
        inline_ids = set()
        ids_to_check = []

        for resource_id in resource_ids:
            if _get_data_directly(resource_id) is not None:
                inline_ids.add(resource_id)
            else:
                ids_to_check.append(resource_id)

        existing_ids = self._do_get_existing_files(ids_to_check) | inline_ids

        return [(resource_id in existing_ids) for resource_id in resource_ids]

# -*- coding: utf-8 -*-

from django.conf import settings

_storage = None


def create_storage():
    global _storage

    if _storage is None:
        if settings.STORAGE_DIR:
            from .storage_fs import FileSystemStorage
            _storage = FileSystemStorage(settings.STORAGE_DIR)
        if settings.MONGODB_URI:
            from .storage_gridfs import GridFsStorage
            _storage = GridFsStorage(settings.MONGODB_URI)

    return _storage

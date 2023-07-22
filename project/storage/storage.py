# -*- coding: utf-8 -*-

from django.conf import settings


def create_storage():
    from .storage_fs import FileSystemStorage
    return FileSystemStorage(settings.STORAGE_DIR)

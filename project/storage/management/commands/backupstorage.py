# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import os
import zipfile
import errno
import six

from django.core.management.base import BaseCommand

from storage.storage import create_storage

ARCHIVE_NAME_FORMAT = 'fs.{:04}.zip'
ARCHIVE_TMP_NAME_FORMAT = 'fs.{:04}.tmp'


def mkdirs(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if errno.EEXIST != e.errno:
            raise


def read_backup(backup_dir):
    n = 0
    present_ids = set()
    while True:
        archive_path = os.path.join(backup_dir, ARCHIVE_NAME_FORMAT.format(n))
        if not os.path.exists(archive_path):
            break
        with zipfile.ZipFile(archive_path, mode='r') as zf:
            for name in zf.namelist():
                present_ids.add(six.text_type(name))
        n += 1
    return n, present_ids


class ArchiveWriter(object):
    def __init__(self, logger, backup_dir, ndx, max_files=100000):
        self._logger = logger
        self._backup_dir = backup_dir
        self._ndx = ndx
        self._max_files = max_files
        self._open()

    def add(self, resource_id_str, path):
        if self._files_added >= self._max_files:
            self._flush(True)
            self._ndx += 1
            self._open()

        self._zf.write(path, resource_id_str)
        self._files_added += 1

    def __enter__(self):
        return self

    def __exit__(self, exctype, excvalue, tb):
        self._flush(exctype is None)

    def _open(self):
        self._files_added = 0
        self._zf = zipfile.ZipFile(self._tmp_path(), mode='w', compression=zipfile.ZIP_DEFLATED, allowZip64=True)

    def _final_path(self):
        return os.path.join(self._backup_dir, ARCHIVE_NAME_FORMAT.format(self._ndx))

    def _tmp_path(self):
        return os.path.join(self._backup_dir, ARCHIVE_TMP_NAME_FORMAT.format(self._ndx))

    def _flush(self, normal_mode):
        self._zf.close()
        self._zf = None

        if normal_mode and self._files_added > 0:
            self._logger.info('Volume #%04d: %d files added', self._ndx, self._files_added)
            # give a permanent name to the archive
            os.rename(self._tmp_path(), self._final_path())
        else:
            # delete the empty archive
            os.unlink(self._tmp_path())


class Command(BaseCommand):
    help = 'Creates an incremental backup'

    def add_arguments(self, parser):
        parser.add_argument('target-dir', help='backup directory')

    def handle(self, *args, **options):
        logger = logging.getLogger('irunner_import')

        target_dir = options['target-dir']
        logger.info('Backup dir: %s', target_dir)

        mkdirs(target_dir)
        n, present_ids = read_backup(target_dir)
        logger.info('Volumes present: %d, resources: %d', n, len(present_ids))

        storage = create_storage()
        total = 0
        added = 0

        with ArchiveWriter(logger, target_dir, n) as wr:
            for resource_id, size in storage.list_all():
                total += 1
                if total % 1000 == 0:
                    logger.info('%d: %d new files added', total, added)
                resource_id_str = six.text_type(resource_id)
                if resource_id_str in present_ids:
                    continue
                src = os.path.join(storage._directory, resource_id_str[:2], resource_id_str)
                wr.add(resource_id_str, src)
                added += 1

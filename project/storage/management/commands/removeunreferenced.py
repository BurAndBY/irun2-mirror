# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import os
import zipfile

from django.core.management.base import BaseCommand

from storage.storage import create_storage


class Command(BaseCommand):
    help = 'Removes unreferenced files from storage'

    def add_arguments(self, parser):
        parser.add_argument('db_dump', help='tsv file')
        parser.add_argument('-t', '--target-dir', help='recycle bin directory')
        parser.add_argument('-z', '--zip-file', help='use ZIP archive as recycle bin')
        parser.add_argument('-d', '--delete', help='just delete', action='store_true')

    def handle(self, *args, **options):
        logger = logging.getLogger('irunner_import')

        target_dir = options['target_dir']
        if target_dir is not None:
            if not os.path.isdir(target_dir):
                raise ValueError('Not a directory')

        zipf = None
        if options['zip_file'] is not None:
            zipf = zipfile.ZipFile(options['zip_file'], mode='w', compression=zipfile.ZIP_DEFLATED, allowZip64=True)

        should_delete = options['delete']

        storage = create_storage()
        with open(options['db_dump']) as fd:
            for line in fd:
                resource_id, _ = line.rstrip().split('\t', 1)
                logger.info('%s', resource_id)
                src = os.path.join(storage._directory, resource_id[:2], resource_id)

                if zipf is not None:
                    zipf.write(src, resource_id)
                if target_dir is not None:
                    os.rename(
                        src,
                        os.path.join(target_dir, resource_id)
                    )
                if should_delete:
                    os.remove(src)

        if zipf is not None:
            zipf.close()

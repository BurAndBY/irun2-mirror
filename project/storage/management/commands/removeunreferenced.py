# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.core.management.base import BaseCommand

from storage.storage import create_storage


class Command(BaseCommand):
    help = 'Removes unreferenced files from storage'

    def add_arguments(self, parser):
        parser.add_argument('db_dump', help='tsv file')
        parser.add_argument('target_dir', help='recycle bin')

    def handle(self, *args, **options):
        target = options['target_dir']
        if not os.path.isdir(target):
            raise ValueError('Not a directory')

        storage = create_storage()
        with open(options['db_dump']) as fd:
            for line in fd:
                resource_id, _ = line.rstrip().split('\t', 1)
                os.rename(
                    os.path.join(storage._directory, resource_id[:2], resource_id),
                    os.path.join(target, resource_id)
                )

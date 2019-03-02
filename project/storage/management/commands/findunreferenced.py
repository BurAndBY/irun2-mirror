# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.core.management.base import BaseCommand
from django.template.defaultfilters import filesizeformat


class Command(BaseCommand):
    help = 'Checks references'

    def add_arguments(self, parser):
        parser.add_argument('db_dump', help='tsv file')
        parser.add_argument('fs_dump', help='tsv file')
        parser.add_argument('unref_dump', help='tsv file')

    def handle(self, *args, **options):
        logger = logging.getLogger('irunner_import')

        db = set()
        with open(options['db_dump']) as fd:
            for line in fd:
                resource_id, _ = line.rstrip().split('\t', 1)
                db.add(resource_id)

        referenced_count = 0
        referenced_size = 0
        unreferenced_count = 0
        unreferenced_size = 0

        unreferenced = []

        fs = {}
        with open(options['fs_dump']) as fd:
            for line in fd:
                resource_id, size = line.rstrip().split('\t')
                size = int(size)
                fs[resource_id] = size
                if resource_id in db:
                    referenced_count += 1
                    referenced_size += size
                else:
                    unreferenced_count += 1
                    unreferenced_size += size
                    unreferenced.append(resource_id)

        logger.info('%d files on disk are referenced in DB (%s)', referenced_count, filesizeformat(referenced_size))
        logger.info('%d files on disk are unreferenced in DB (%s)', unreferenced_count, filesizeformat(unreferenced_size))

        with open(options['unref_dump'], 'w') as fd:
            for r in unreferenced:
                fd.write('{}\t{}\n'.format(r, fs[r]))

        broken = 0
        for resource_id in db:
            if resource_id not in fs:
                broken += 1

        logger.info('%d links in DB are broken', broken)

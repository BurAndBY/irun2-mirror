# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.core.management.base import BaseCommand

from storage.storage import create_storage


class Command(BaseCommand):
    help = 'Dumps resource ids that are present on disk'

    def add_arguments(self, parser):
        parser.add_argument('dump', help='tsv file')

    def handle(self, *args, **options):
        logger = logging.getLogger('irunner_import')
        prefix = None
        storage = create_storage()

        with open(options['dump'], 'w') as fd:
            for resource_id, size in storage.list_all():
                key = str(resource_id)
                if key[:2] != prefix:
                    prefix = key[:2]
                    logger.info('Prefix %s', prefix)

                fd.write('{}\t{}\n'.format(key, size))

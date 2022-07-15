# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from common.outcome import Outcome
from solutions.models import Judgement, TestCaseResult
from storage.storage import create_storage

import logging
import zipfile


MAX_SIZE = 100 * (1 << 20)


class Command(BaseCommand):
    help = 'Exports accepted outputs'

    def add_arguments(self, parser):
        parser.add_argument('problem', help='problem id to export', type=int)
        parser.add_argument('zipfile', help='zip file to write')

    def handle(self, *args, **options):
        logger = logging.getLogger('irunner_import')
        problem_id = options['problem']

        storage = create_storage()

        with zipfile.ZipFile(options['zipfile'], mode='w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            for testcaseresult in TestCaseResult.objects.filter(
                    test_case__problem_id=problem_id,
                    output_resource_id__isnull=False,
                    outcome=Outcome.ACCEPTED).select_related('judgement', 'test_case'):
                resource_id = testcaseresult.output_resource_id
                blob = b'hello'
                blob, is_complete = storage.read_blob(resource_id, max_size=MAX_SIZE)
                assert is_complete
                fn = 's{}_j{}_t{:02d}.txt'.format(
                    testcaseresult.judgement.solution_id,
                    testcaseresult.judgement_id,
                    testcaseresult.test_case.ordinal_number
                )
                logger.info('Write %s', fn)
                zf.writestr(fn, blob)

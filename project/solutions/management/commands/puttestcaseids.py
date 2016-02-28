# -*- coding: utf-8 -*-

from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware

from common.irunner_import import connect_irunner_db, fetch_irunner_file
from common.memory_string import parse_memory
from solutions.models import Solution, Judgement, Outcome, TestCaseResult
from problems.models import Problem, TestCase
from storage.storage import create_storage
from storage.models import FileMetadata

import logging


class Command(BaseCommand):
    help = 'Imports solutions from iRunner'

    def add_arguments(self, parser):
        parser.add_argument('first_judgement_id', type=int)
        parser.add_argument('last_judgement_id', type=int)

    def handle(self, *args, **options):
        logger = logging.getLogger('irunner_import')

        for judgement in Judgement.objects.\
                filter(pk__gte=options['first_judgement_id'], pk__lte=options['last_judgement_id']).\
                select_related('solution', 'solution__problem'):
            logger.info('Processing judgement %d', judgement.id)

            has_ids = 0

            test_case_results = judgement.testcaseresult_set.order_by('id')
            all_tcr = len(test_case_results)

            for tcr in test_case_results:
                if tcr.test_case_id is not None:
                    has_ids += 1

            if has_ids == all_tcr or has_ids > 0:
                logger.warning('%d links of %d are present, skip', has_ids, all_tcr)
                continue

            test_case_ids = judgement.solution.problem.testcase_set.\
                all().order_by('ordinal_number').values_list('id', flat=True)

            if len(test_case_ids) != len(test_case_results):
                logger.error('number of tests has been changed: %d results, but %d tests in the problem', len(test_case_results), len(test_case_ids))

            with transaction.atomic():
                for tcr, tid in zip(test_case_results, test_case_ids):
                    tcr.test_case_id = tid
                    tcr.save(update_fields=['test_case_id'])

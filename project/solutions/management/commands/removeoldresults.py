# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from django.db.models import Q

from solutions.models import Judgement, TestCaseResult
import logging
import argparse
import datetime

FORMAT = '%Y-%m-%d'


def valid_date(s):
    try:
        return datetime.datetime.strptime(s, FORMAT)
    except ValueError:
        msg = 'Not a valid date: "{0}".'.format(s)
        raise argparse.ArgumentTypeError(msg)


class Command(BaseCommand):
    help = 'Removes old judging results'

    def add_arguments(self, parser):
        parser.add_argument('date', help='YYYY-MM-DD', type=valid_date)
        parser.add_argument('--do', action='store_true')

    def handle(self, *args, **options):
        logger = logging.getLogger('irunner_import')

        ts = options['date']
        ts = make_aware(ts)

        test_cases = TestCaseResult.objects\
            .filter(judgement__extra_info__finish_testing_time__lt=ts)\
            .filter(
                Q(output_resource_id__isnull=False) |
                Q(stdout_resource_id__isnull=False) |
                Q(stderr_resource_id__isnull=False)
            )

        if options['do']:
            rows_updated = test_cases.update(output_resource_id=None, stdout_resource_id=None, stderr_resource_id=None)
            logger.info('%d rows updated', rows_updated)
        else:
            judgements = Judgement.objects.filter(extra_info__finish_testing_time__lt=ts).order_by('-id')
            logger.info('%d judgements before %s to process', judgements.count(), ts.strftime(FORMAT))
            logger.info('%s...', ', '.join([str(j.id) for j in judgements[:10]]))
            logger.info('%d test cases to process', test_cases.count())

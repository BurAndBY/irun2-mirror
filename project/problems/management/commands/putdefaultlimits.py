# -*- coding: utf-8 -*-

import logging
from collections import Counter

from django.core.management.base import BaseCommand

from problems.models import Problem, ProblemExtraInfo, TestCase


class Command(BaseCommand):
    help = 'Deduces time and memory limits for the whole problems from individual limits per test'

    def process(self, logger, problem_id):
        time_limits = Counter()
        memory_limits = Counter()
        has_tests = False
        for time_limit, memory_limit in TestCase.objects.filter(problem_id=problem_id).values_list('time_limit', 'memory_limit'):
            time_limits[time_limit] += 1
            memory_limits[memory_limit] += 1
            has_tests = True

        if len(time_limits) > 1 or len(memory_limits) > 1:
            for tl, cnt in time_limits.most_common():
                logger.info('> TL %d: %d', tl, cnt)
            for ml, cnt in memory_limits.most_common():
                logger.info('> ML %d: %d', ml, cnt)

        if has_tests:
            tl, _ = time_limits.most_common(1)[0]
            ml, _ = memory_limits.most_common(1)[0]
            logger.debug('= setting TL = %d, ML = %d', tl, ml)
            ProblemExtraInfo.objects.update_or_create(pk=problem_id, defaults={'default_time_limit': tl, 'default_memory_limit': ml})

    def handle(self, *args, **options):
        logger = logging.getLogger('irunner_import')

        problem_ids = Problem.objects.all().values_list('pk', flat=True)
        logger.info('%d problems', len(problem_ids))

        for problem_id in problem_ids:
            logger.info('problem %d', problem_id)
            self.process(logger, problem_id)

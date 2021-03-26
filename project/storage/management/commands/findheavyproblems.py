# -*- coding: utf-8 -*-

import logging
from collections import defaultdict

from django.core.management.base import BaseCommand

from solutions.models import TestCaseResult
from storage.storage import create_storage


class ResourceCollector(object):
    def __init__(self):
        self._ins = set()
        self._outs = set()

    def add(self, resource_id, tag):
        if resource_id is None:
            return
        if tag in ('stdout', 'stderr', 'output'):
            self._outs.add(resource_id)
        else:
            self._ins.add(resource_id)

    @property
    def count(self):
        return len(self._ins | self._outs)

    def calc_total_size(self, files):
        return sum(files.get(resource_id, 0) for resource_id in (self._ins | self._outs))

    def calc_outputs_size(self, files):
        return sum(files.get(resource_id, 0) for resource_id in (self._outs - self._ins))


def _collect_real_files(logger):
    storage = create_storage()
    prefix = None
    files = {}
    for resource_id, size in storage.list_all():
        key = str(resource_id)
        if key[:2] != prefix:
            prefix = key[:2]
            logger.info('Prefix %s', prefix)
        files[resource_id] = size
    return files


class Command(BaseCommand):
    help = 'Finds the heaviest problems'

    def handle(self, *args, **options):
        logger = logging.getLogger('irunner_import')

        logger.info('> TestCaseResult')
        collectors = defaultdict(ResourceCollector)
        n = 0
        for inf, ouf, ans, stdout, stderr, problem_id in TestCaseResult.objects.values_list(
                'input_resource_id',
                'output_resource_id',
                'answer_resource_id',
                'stdout_resource_id',
                'stderr_resource_id',
                'judgement__solution__problem_id'
                ):
            collector = collectors[problem_id]
            collector.add(inf, 'input')
            collector.add(ouf, 'output')
            collector.add(ans, 'answer')
            collector.add(stdout, 'stdout')
            collector.add(stderr, 'stderr')
            n += 1
            if n % 100000 == 0:
                logger.info('%d test cases...', n)

        files = _collect_real_files(logger)
        for problem_id, collector in collectors.items():
            print('{}\t{}\t{}\t{}'.format(problem_id, collector.count, collector.calc_total_size(files), collector.calc_outputs_size(files)))

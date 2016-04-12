# -*- coding: utf-8 -*-

import logging
from django.core.management.base import BaseCommand

from common.irunner_import import connect_irunner_db
from contests.models import ContestSolution
from solutions.models import Solution


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('old_contest_id', type=int)
        parser.add_argument('new_contest_id', type=int)

    def handle(self, *args, **options):
        logger = logging.getLogger('irunner_import')

        db = connect_irunner_db()

        cur = db.cursor()
        cur.execute('''SELECT solutionID FROM irunner_solution WHERE contestId = %s''', (options['old_contest_id'],))
        solution_ids = set(row[0] for row in cur)
        logger.info('%d solutions found in iRunner', len(solution_ids))

        present_solution_ids = set(Solution.objects.filter(pk__in=solution_ids).values_list('pk', flat=True))
        logger.info('%d matching solutions found in iRunner2', len(present_solution_ids))

        objs = [ContestSolution(contest_id=options['new_contest_id'], solution_id=solution_id) for solution_id in present_solution_ids]
        ContestSolution.objects.bulk_create(objs)

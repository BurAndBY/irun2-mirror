# -*- coding: utf-8 -*-

from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware

from common.outcome import Outcome
from common.irunner_import import connect_irunner_db, fetch_irunner_file
from common.memory_string import parse_memory
from solutions.models import Solution, Judgement, TestCaseResult
from problems.models import Problem, TestCase
from storage.storage import create_storage
from storage.models import FileMetadata

import logging


def _unpack_status(status):
    new_status = {
        0: Judgement.WAITING,
        1: Judgement.COMPILING,
        2: Judgement.TESTING,
        3: Judgement.DONE,
    }.get(status)

    if new_status is None:
        raise ValueError('Unable to deduce solution status from {0}'.format(status))

    return new_status


def _unpack_error(error):
    new_error = {
        0: Outcome.ACCEPTED,
        1: Outcome.WRONG_ANSWER,
        2: Outcome.PRESENTATION_ERROR,
        3: Outcome.CHECK_FAILED,
        4: Outcome.COMPILATION_ERROR,
        5: Outcome.TIME_LIMIT_EXCEEDED,
        6: Outcome.RUNTIME_ERROR,
        7: Outcome.MEMORY_LIMIT_EXCEEDED,
    }.get(error)

    if new_error is None:
        raise ValueError('Unable to deduce solution error from {0}'.format(error))

    return new_error


def _unpack_state(x):
    status = x & 0x7
    error = (x >> 4) & 0x7
    # is_accepted = ((x & 0x8) != 0)
    number = (x >> 7) & 0xFFFF

    new_status = _unpack_status(status)
    new_error = _unpack_error(error)
    new_number = number if new_error != Outcome.CHECK_FAILED else 0

    return (new_status, new_error, new_number)


def _get_memory_limit(db, problem_id):
    cur = db.cursor()

    cur.execute('SELECT memoryLimit FROM irunner_task WHERE taskID = %s', (problem_id,))
    row = cur.fetchone()
    return parse_memory(row[0]) if (row and row[0]) else 0


def _fetch_test_results(db, storage, logger, problem_id, solution_id):
    memory_limit = _get_memory_limit(db, problem_id)

    cur = db.cursor()

    test_ids = set(TestCase.objects.filter(problem_id=problem_id).values_list('id', flat=True))

    cur.execute('''SELECT testResultID, errorType, irunner_testresult.testID,
                          memoryUsed, exitCode, checkerStr,
                          irunner_test.points, irunner_testresult.points,
                          irunner_test.time, irunner_testresult.timeExecution
                   FROM irunner_testresult JOIN irunner_test USING(testID)
                   WHERE solutionID = %s''', (solution_id,))

    for row in cur:
        test_case_id = row[2]
        if test_case_id not in test_ids:
            logger.warning('Got test %d that does not exist', test_case_id)
            test_case_id = None

        TestCaseResult.objects.update_or_create(id=row[0], defaults={
            'judgement_id': solution_id,
            'outcome': _unpack_error(row[1]),
            'test_case_id': test_case_id,
            'memory_limit': memory_limit,
            'memory_used': row[3],
            'exit_code': row[4],
            'checker_message': row[5] or '',
            'max_score': int(row[6]),
            'score': int(row[7]),
            'time_limit': int(row[8] * 1000),
            'time_used': row[9],
        })


class Command(BaseCommand):
    help = 'Imports solutions from iRunner'

    def handle(self, *args, **options):
        logger = logging.getLogger('irunner_import')
        db = connect_irunner_db()
        storage = create_storage()

        present_users = set(get_user_model().objects.all().values_list('id', flat=True))
        present_problems = set(Problem.objects.all().values_list('id', flat=True))

        cur = db.cursor()
        cur.execute('SELECT solutionID, taskID, languageID, fileID, status, receivedTime, senderIP, userID FROM irunner_solution')

        for row in cur.fetchall():
            solution_id = row[0]
            problem_id = row[1]
            compiler_id = row[2]
            file_id = row[3]
            irunner_state = row[4]
            reception_time = row[5]
            sender_ip = row[6]
            user_id = row[7]

            logger.info('Importing solution %d...', solution_id)

            if not user_id:
                logger.warning('Solution %d has %s user set', solution_id, user_id)
                continue
            if user_id not in present_users:
                logger.warning('Solution %d has user %d that does not exist', solution_id, user_id)
                continue

            if problem_id not in present_problems:
                logger.warning('Solution belongs to problem %d that does not exist', problem_id)
                continue

            file_fetched = fetch_irunner_file(db, file_id, storage)
            if file_fetched is None:
                logger.warning('Unable to fetch source code for solution %d', solution_id)
                continue
            filename, size, resource_id = file_fetched

            status, outcome, number = _unpack_state(irunner_state)

            with transaction.atomic():
                metadata = FileMetadata(
                    filename=filename,
                    size=size,
                    resource_id=resource_id,
                )
                metadata.save()

                solution, _ = Solution.objects.update_or_create(id=solution_id, defaults={
                    'problem_id': problem_id,
                    'source_code': metadata,
                    'compiler_id': compiler_id,
                    'reception_time': make_aware(reception_time),
                    'ip_address': sender_ip,
                    'author_id': user_id,
                })

                judgement, _ = Judgement.objects.update_or_create(id=solution_id, defaults={
                    'solution_id': solution_id,
                    'status': status,
                    'outcome': outcome,
                    'test_number': number,
                })

                solution.best_judgement = judgement
                solution.save()

                _fetch_test_results(db, storage, logger, problem_id, solution_id)

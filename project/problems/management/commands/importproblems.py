# -*- coding: utf-8 -*-

import logging
import re

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from common.memory_string import parse_memory
from common.irunner_import import connect_irunner_db
from problems.models import Problem, ProblemExtraInfo, ProblemRelatedFile, ProblemRelatedSourceFile, ProblemFolder
from storage.storage import create_storage


def int_or_none(obj):
    return int(obj) if obj is not None else None


def _split_name(s):
    number = None
    subnumber = None
    name = ''
    difficulty = None  # TODO

    rx = re.compile(r'^((?P<number>\d+)(\.(?P<subnumber>\d+))?)?\.?\s*(?P<name>[^\[]*)(\[(?P<difficulty>\d{1,2})\])?$')
    m = rx.match(s)
    if m is not None:
        number = int_or_none(m.group('number'))
        subnumber = int_or_none(m.group('subnumber'))
        name = m.group('name')
        difficulty = int_or_none(m.group('difficulty'))
    else:
        name = s
    return (number, subnumber, name, difficulty)


def _import_problem_tree(db, folder_id, obj=None):
    cur = db.cursor()
    cur.execute('SELECT folderID, name FROM katrin_folder WHERE parentID = %s', (folder_id,))
    rows = cur.fetchall()
    for row in rows:
        next_folder_id, name = row[0], row[1]
        folder, _ = ProblemFolder.objects.update_or_create(id=next_folder_id, defaults={
            'name': name,
            'parent': obj
        })
        _import_problem_tree(db, next_folder_id, folder)


class Command(BaseCommand):
    help = 'Does some magical work'

    def add_arguments(self, parser):
        parser.add_argument('first_problem_id', nargs='?', type=int)
        parser.add_argument('last_problem_id', nargs='?', type=int)

    def _parse_options(self, options):
        first_problem_id = options['first_problem_id']
        if first_problem_id is not None:
            last_problem_id = options['last_problem_id']
            if last_problem_id is None:
                last_problem_id = first_problem_id
        else:
            first_problem_id = 1
            last_problem_id = 10000
        return first_problem_id, last_problem_id

    def handle(self, *args, **options):
        logger = logging.getLogger('irunner_import')

        first_problem_id, last_problem_id = self._parse_options(options)
        logger.info('Problems to import: from %d to %d', first_problem_id, last_problem_id)

        db = connect_irunner_db()

        ROOT_FOLDER = 4
        with transaction.atomic():
            with ProblemFolder.objects.delay_mptt_updates():
                _import_problem_tree(db, ROOT_FOLDER)

        cur = db.cursor()
        cur.execute('''SELECT taskID, shortName, name, memoryLimit, taskGroupID, author, offered, place, authorContacts
                       FROM irunner_task WHERE taskId >= %s AND taskId <= %s''', (first_problem_id, last_problem_id))

        storage = create_storage()

        for row in cur.fetchall():
            with transaction.atomic():
                task_id = int(row[0])
                logger.info('Importing problem %d...', task_id)

                problem, created = Problem.objects.get_or_create(id=task_id)

                short_number, short_subnumber, short_name, short_difficulty = _split_name(row[1])
                full_number, full_subnumber, full_name, full_difficulty = _split_name(row[2])
                memory_limit = parse_memory(row[3]) if row[3] else 0
                folder_id = row[4]

                description = u'\n'.join([unicode(t) for t in row[5:9] if t])

                problem.number = full_number
                problem.subnumber = full_subnumber
                problem.short_name = short_name.strip()
                problem.full_name = full_name.strip()
                problem.difficulty = full_difficulty or short_difficulty

                subc = db.cursor()

                input_mf_id = None
                output_mf_id = None

                subc.execute('''SELECT userFileName, fileTypeID, metafileID FROM irunner_metafile WHERE taskID = %s''', (task_id, ))
                for subrow in subc:
                    if subrow[1] == 10032:
                        problem.input_filename = subrow[0]
                        input_mf_id = subrow[2]
                    elif subrow[1] == 10033:
                        problem.output_filename = subrow[0]
                        output_mf_id = subrow[2]

                problem.save()

                tests = {}

                subc.execute('''SELECT testID, description, points, time FROM irunner_test WHERE taskID = %s ORDER BY testID''', (task_id, ))
                for i, r in enumerate(subc):
                    test_id = r[0]
                    defaults = {
                        'description': (r[1] or ''),
                        'points': int(r[2]),
                        'time_limit': (int(r[3] * 1000)),
                        'memory_limit': memory_limit,
                        'ordinal_number': i + 1,
                    }
                    tests[test_id], inserted = problem.testcase_set.update_or_create(id=test_id, defaults=defaults)
                    if inserted:
                        logger.info('> new test %d', test_id)

                for test_id, tc in tests.iteritems():
                    subc.execute('''SELECT metafileID, data FROM irunner_test_file JOIN katrin_file ON irunner_test_file.fileID = katrin_file.fileID WHERE testID = %s''', (test_id, ))
                    for r in subc:
                        if r[0] == input_mf_id:
                            res = tc.set_input(storage, ContentFile(r[1]))
                            if res:
                                logger.info('> test %d: new input', test_id)
                        if r[0] == output_mf_id:
                            res = tc.set_answer(storage, ContentFile(r[1]))
                            if res:
                                logger.info('> test %d: new answer', test_id)

                # extra info
                if description:
                    ProblemExtraInfo.objects.update_or_create(problem_id=problem.id, defaults={'description': description})

                folder = ProblemFolder.objects.filter(id=folder_id).first()
                if folder is not None:
                    problem.folders.add(folder)
                    problem.save()

                for tc in tests.itervalues():
                    tc.save()

                subc = db.cursor()
                subc.execute('''SELECT taskFileID, languageID, name, fileTypeID, data, description
                    FROM irunner_taskfile JOIN katrin_file ON irunner_taskfile.fileID = katrin_file.fileID
                    WHERE taskID = %s''', (task_id,))

                for subrow in subc:
                    #print task_id, subrow
                    task_file_id = int(subrow[0])
                    compiler_id = subrow[1]
                    file_type = subrow[3]
                    description = subrow[5] or ''

                    data = subrow[4]
                    filename = subrow[2]
                    resource_id = storage.save(ContentFile(data))

                    defaults = {
                        'problem': problem,
                        'file_type': file_type,
                        'description': description,
                        'filename': filename,
                        'resource_id': resource_id,
                        'size': len(data)
                    }

                    if compiler_id:
                        defaults['compiler_id'] = compiler_id
                        ProblemRelatedSourceFile.objects.update_or_create(id=task_file_id, defaults=defaults)
                    else:
                        ProblemRelatedFile.objects.update_or_create(id=task_file_id, defaults=defaults)

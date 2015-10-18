# -*- coding: utf8 -*-

from django.core.management.base import BaseCommand, CommandError
from problems.models import Problem, ProblemRelatedFile
from storage.storage import create_storage, ResourceId
from django.core.files.base import ContentFile


#import mysql.connector
import MySQLdb

from django.db import transaction
import re


def _split_name(s):
    number = ''
    name = ''
    complexity = None  # TODO

    rx = re.compile(r'^(\d+(\.\d+)?)?\.?\s*(.*)$')
    m = rx.match(s)
    if m is not None:
        number = m.group(1)
        name = m.group(3)
    else:
        name = s
    return (number, name, complexity)


class Command(BaseCommand):
    help = 'Does some magical work'

    def handle(self, *args, **options):
        db = MySQLdb.connect(user='irunner_user', passwd='irunner_localhost',
                             host='127.0.0.1',
                             port=3307,
                             db='irunner',
                             charset='utf8')

        cur = db.cursor()
        cur.execute('SELECT taskID, shortName, name FROM irunner_task')

        storage = create_storage()

        with transaction.atomic():
            for row in cur.fetchall()[:500]:
                task_id = int(row[0])
                problem, created = Problem.objects.get_or_create(id=task_id)

                short_number, short_name, short_complexity = _split_name(row[1])
                full_number, full_name, full_complexity = _split_name(row[2])

                problem.number = full_number or short_number or ''
                problem.short_name = short_name.strip()
                problem.full_name = full_name.strip()
                problem.complexity = full_complexity or short_complexity

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

                problem.testcase_set.all().delete()
                tests = {}

                subc.execute('''SELECT testID, description, points, time FROM irunner_test WHERE taskID = %s ORDER BY testID''', (task_id, ))
                for i, r in enumerate(subc):
                    test_id = r[0]
                    tests[test_id] = problem.testcase_set.create(
                        id=test_id,
                        description=(r[1] or ''),
                        points=int(r[2]),
                        time_limit=(int(r[3] * 1000)),
                        ordinal_number=i+1
                    )

                for test_id, tc in tests.iteritems():
                    subc.execute('''SELECT metafileID, data FROM irunner_test_file JOIN katrin_file ON irunner_test_file.fileID = katrin_file.fileID WHERE testID = %s''', (test_id, ))
                    for r in subc:
                        if r[0] == input_mf_id:
                            tc.set_input(storage, ContentFile(r[1]))
                        if r[0] == output_mf_id:
                            tc.set_answer(storage, ContentFile(r[1]))

                for tc in tests.itervalues():
                    tc.save()

                problem.save()

                subc = db.cursor()
                subc.execute('''SELECT taskFileID, flag, name, fileTypeID, data, description
                    FROM irunner_taskfile JOIN katrin_file ON irunner_taskfile.fileID = katrin_file.fileID
                    WHERE taskID = %s''', (task_id,))

                for subrow in subc:
                    #print task_id, subrow
                    task_file_id = int(subrow[0])

                    data = subrow[4]
                    resource_id = storage.save(ContentFile(data))

                    related_file, created = ProblemRelatedFile.objects.update_or_create(id=task_file_id, defaults={
                        'problem': problem,
                        'file_type': subrow[3],
                        'is_public': (subrow[1] != 1),
                        'name': subrow[2],
                        'size': len(data),
                        'description': subrow[5] or '',
                        'resource_id': resource_id
                        })
                    related_file.save()

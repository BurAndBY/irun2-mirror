# -*- coding: utf-8 -*-

import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import make_aware

from common.irunner_import import connect_irunner_db
from contests.models import Message


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('old_contest_id', type=int)
        parser.add_argument('new_contest_id', type=int)

    def handle(self, *args, **options):
        logger = logging.getLogger('irunner_import')

        db = connect_irunner_db()

        cur = db.cursor()
        cur.execute('''SELECT senderID, subject, message, date, flag, type, parentID, recepientID, taskID, messageID
                       FROM katrin_message
                       WHERE contestId = %s ORDER BY messageID''', (options['old_contest_id'],))

        old_to_new = {}

        with transaction.atomic():
            for row in cur:
                flag = row[4]
                msg = Message(sender_id=row[0],
                              subject=row[1],
                              text=row[2],
                              timestamp=make_aware(row[3]),
                              is_answered=(row[5] == Message.QUESTION and flag != 0),
                              message_type=row[5],
                              parent_id=old_to_new[row[6]] if row[6] else None,
                              recipient_id=row[7] if (row[7] and flag == 2) else None,
                              problem_id=row[8] if row[8] else None,
                              contest_id=options['new_contest_id'])
                msg.save()

                old_id = row[9]
                new_id = msg.id
                old_to_new[old_id] = new_id
                logger.info('message %d has been imported as %d', old_id, new_id)

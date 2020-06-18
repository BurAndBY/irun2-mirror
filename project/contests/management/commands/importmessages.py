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

        ids = set()
        cur.execute('''SELECT messageID, parentID FROM katrin_message WHERE contestId = %s''', (options['old_contest_id'],))
        for message_id, parent_id in cur:
            assert message_id
            ids.add(message_id)

        if ids:
            ids_str = ', '.join(str(id) for id in ids)
            cur.execute('''SELECT messageID, parentID FROM katrin_message WHERE parentID IN ({})'''.format(ids_str))
            for message_id, parent_id in cur:
                assert message_id > parent_id
                ids.add(message_id)

        logger.info('importing %d messages...', len(ids))

        old_to_new = {}

        with transaction.atomic():
            for message_id in sorted(ids):
                cur.execute('''SELECT senderID, subject, message, date, flag, type, parentID, recepientID, taskID
                   FROM katrin_message
                   WHERE messageID = %s''', (message_id,))

                row = cur.fetchone()

                sender_id = row[0]
                if sender_id == 0:  # sender: Guest
                    continue

                parent_id = row[6]
                if parent_id != 0 and parent_id not in old_to_new:  # parent message was skipped
                    continue

                flag = row[4]
                msg = Message(sender_id=sender_id,
                              subject=row[1],
                              text=row[2],
                              timestamp=make_aware(row[3]),
                              is_answered=(row[5] == Message.QUESTION and flag != 0),
                              message_type=row[5],
                              parent_id=old_to_new[parent_id] if parent_id else None,
                              recipient_id=row[7] if (row[7] and flag == 2) else None,
                              problem_id=row[8] if row[8] else None,
                              contest_id=options['new_contest_id'])
                msg.save()

                old_id = message_id
                new_id = msg.id
                old_to_new[old_id] = new_id
                logger.info('message %d has been imported as %d', old_id, new_id)

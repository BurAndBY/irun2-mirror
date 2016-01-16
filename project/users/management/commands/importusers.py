# -*- coding: utf-8 -*-

import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from common.irunner_import import connect_irunner_db, import_tree
from users.models import UserFolder, UserProfile
from django.contrib import auth


def process_user(row):
    User = auth.get_user_model()

    user_id = int(row[0])
    username = row[1].decode('utf-8')

    user = User()
    user.id = user_id
    user.username = username

    password = row[2]
    if len(password) == 32:
        user.password = 'md5$$' + password
    else:
        user.set_unusable_password()

    user.first_name = row[3] or ''
    user.last_name = row[5] or ''

    email = row[7]
    if email is not None:
        try:
            validate_email(email)
        except ValidationError:
            email = None
    user.email = email or ''

    user.clean_fields()
    user.clean()

    userprofile = UserProfile()
    userprofile.user_id = user_id
    userprofile.patronymic = row[4] or ''
    userprofile.description = row[8] or ''

    folder_id = row[9]
    if folder_id is not None and UserFolder.objects.filter(pk=folder_id).count() != 1:
        folder_id = None

    userprofile.folder_id = folder_id
    userprofile.clean_fields(exclude=['user'])
    userprofile.clean()

    user.save()
    userprofile.save()


class Command(BaseCommand):
    help = 'Does some magical work'

    def handle(self, *args, **options):
        logger = logging.getLogger('irunner_import')
        db = connect_irunner_db()

        ROOT_FOLDER = 1
        with transaction.atomic():
            with UserFolder.objects.delay_mptt_updates():
                import_tree(UserFolder, db, ROOT_FOLDER)

        cur = db.cursor()
        cur.execute('SELECT userID, login, password, firstName, middleName, lastName, removed, email, description, userGroupID FROM katrin_user WHERE userID > 0')

        for row in cur.fetchall():
            try:
                with transaction.atomic():
                    process_user(row)
            except Exception as e:
                logger.error(u'Skipped user %d "%s":\n%s', row[0], row[1].decode('utf-8', errors='replace'), e)

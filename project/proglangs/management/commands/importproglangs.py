# -*- coding: utf8 -*-

import re

from django.core.management.base import BaseCommand

from common.irunner_import import connect_irunner_db
from proglangs.models import ProgrammingLanguage as PL


def _is_legacy(handle):
    return handle in ('BP7', 'FP2', 'CSHARP11', 'MSVC')

FAMILIES = {
    'FP': PL.PASCAL,
    'BP': PL.PASCAL,
    'BC': PL.CPP,
    'JAVA': PL.JAVA,
    'PY': PL.PYTHON,
    'G': PL.CPP,
    'M': PL.CPP,
    'DELPHI': PL.DELPHI,
    'CS': PL.CSHARP
}


def _get_family(handle):
    if re.match(r'^MVC\d+$', handle):
        return PL.C
    if re.match(r'^GNUC\d+$', handle):
        return PL.C

    for prefix, family in FAMILIES.iteritems():
        if handle.startswith(prefix):
            return family
    return PL.UNKNOWN


class Command(BaseCommand):
    help = 'Imports programming languages from iRunner'

    def handle(self, *args, **options):
        db = connect_irunner_db()

        cur = db.cursor()
        cur.execute('SELECT languageID, title, description FROM irunner_language')

        for row in cur.fetchall():
            handle = row[1]

            programming_language, _ = PL.objects.update_or_create(
                id=row[0],
                defaults={
                    'handle': handle,
                    'description': row[2],
                    'legacy': _is_legacy(handle),
                    'family': _get_family(handle)
                }
            )

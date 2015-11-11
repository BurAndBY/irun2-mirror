# -*- coding: utf8 -*-

import re

from django.core.management.base import BaseCommand

from common.irunner_import import connect_irunner_db
from proglangs.models import Compiler


def _is_legacy(handle):
    return handle in ('BP7', 'FP2', 'CSHARP11', 'MSVC')

LANGUAGES = {
    'FP': Compiler.PASCAL,
    'BP': Compiler.PASCAL,
    'BC': Compiler.CPP,
    'JAVA': Compiler.JAVA,
    'PY': Compiler.PYTHON,
    'G': Compiler.CPP,
    'M': Compiler.CPP,
    'DELPHI': Compiler.DELPHI,
    'CS': Compiler.CSHARP
}


def _get_language(handle):
    if re.match(r'^MVC\d+$', handle):
        return Compiler.C
    if re.match(r'^GNUC\d+$', handle):
        return Compiler.C

    for prefix, language in LANGUAGES.iteritems():
        if handle.startswith(prefix):
            return language
    return Compiler.UNKNOWN


class Command(BaseCommand):
    help = 'Imports programming languages from iRunner'

    def handle(self, *args, **options):
        db = connect_irunner_db()

        cur = db.cursor()
        cur.execute('SELECT languageID, title, description FROM irunner_language')

        for row in cur.fetchall():
            handle = row[1]

            programming_language, _ = Compiler.objects.update_or_create(
                id=row[0],
                defaults={
                    'handle': handle,
                    'description': row[2],
                    'legacy': _is_legacy(handle),
                    'language': _get_language(handle)
                }
            )

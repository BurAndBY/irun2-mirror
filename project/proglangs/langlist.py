from django.db import models
from django.utils.translation import ugettext_lazy as _


class ProgrammingLanguage(models.Model):
    UNKNOWN = ''
    C = 'c'
    CPP = 'cpp'
    JAVA = 'java'
    PASCAL = 'pas'
    DELPHI = 'dpr'
    PYTHON = 'py'
    CSHARP = 'cs'
    SHELL = 'sh'

    CHOICES = (
        (UNKNOWN, _('Unknown')),
        (C, 'C'),
        (CPP, 'C++'),
        (JAVA, 'Java'),
        (PASCAL, 'Pascal'),
        (DELPHI, 'Delphi'),
        (PYTHON, 'Python'),
        (CSHARP, 'C#'),
        (SHELL, 'Shell'),
    )


def get_language_label(x):
    for language, label in ProgrammingLanguage.CHOICES:
        if language == x:
            return label
    return x


def split_language_codes(langs):
    return langs.replace(',', ' ').split()


def list_language_codes():
    for code, name in ProgrammingLanguage.CHOICES:
        if code != ProgrammingLanguage.UNKNOWN:
            yield code

class ProgrammingLanguage(object):
    UNKNOWN = ''
    C = 'c'
    CPP = 'cpp'
    JAVA = 'java'
    KOTLIN = 'kt'
    PASCAL = 'pas'
    DELPHI = 'dpr'
    PYTHON = 'py'
    CSHARP = 'cs'
    SHELL = 'sh'
    ZIP = 'zip'
    ASM = 'asm'

    CHOICES = (
        (UNKNOWN, 'N/A'),
        (C, 'C'),
        (CPP, 'C++'),
        (JAVA, 'Java'),
        (KOTLIN, 'Kotlin'),
        (PASCAL, 'Pascal'),
        (DELPHI, 'Delphi'),
        (PYTHON, 'Python'),
        (CSHARP, 'C#'),
        (SHELL, 'Shell'),
        (ZIP, 'ZIP'),
        (ASM, 'Asm'),
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

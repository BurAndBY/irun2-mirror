import re

from models import Compiler

HIGHLIGHTJS = {
    Compiler.C: 'c',
    Compiler.CPP: 'cpp',
    Compiler.JAVA: 'java',
    Compiler.PASCAL: 'delphi',
    Compiler.DELPHI: 'delphi',
    Compiler.PYTHON: 'py',
    Compiler.CSHARP: 'cs',
}


def get_highlightjs_class(lang):
    return HIGHLIGHTJS.get(lang)


FILENAME_EXTENSIONS = {
    Compiler.C: 'c',
    Compiler.CPP: 'cpp',
    Compiler.JAVA: 'java',
    Compiler.PASCAL: 'pas',
    Compiler.DELPHI: 'dpr',
    Compiler.PYTHON: 'py',
    Compiler.CSHARP: 'cs',
}

PUBLIC_CLASS_REGEX = re.compile(r'^\s*public\s+class\s+([a-zA-Z0-9_]{1,64})')


def _extract_java_public_class(text):
    for line in text.splitlines():
        m = PUBLIC_CLASS_REGEX.match(line)
        if m is not None:
            return m.group(1)


def guess_filename(lang, text):
    name = None

    if lang == Compiler.JAVA:
        public_class = _extract_java_public_class(text)
        if public_class is not None:
            name = public_class

    elif lang == Compiler.CSHARP:
        name = 'Solution'
    else:
        name = 'solution'

    if name is None:
        return None

    extension = FILENAME_EXTENSIONS.get(lang)

    if extension is not None:
        return '{0}.{1}'.format(name, extension)
    else:
        return name

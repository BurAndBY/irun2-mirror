import re

from models import Compiler

HIGHLIGHTJS = {
    Compiler.C: 'c',
    Compiler.CPP: 'cpp',
    Compiler.JAVA: 'java',
    Compiler.PASCAL: 'delphi',
    Compiler.DELPHI: 'delphi',
    Compiler.PYTHON: 'py',
    Compiler.CSHARP: 'csharp',
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

PUBLIC_CLASS_REGEX = re.compile(r'^(?P<ws>\s*)public\s+class\s+(?P<name>[a-zA-Z0-9_]{1,64})')


def _extract_java_public_class(text):
    indent = None
    name = None
    for line in text.splitlines():
        m = PUBLIC_CLASS_REGEX.match(line)
        if m is not None:
            cur_indent = len(m.group('ws'))
            if (indent is None) or (cur_indent < indent):
                indent = cur_indent
                name = m.group('name')
    return name


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

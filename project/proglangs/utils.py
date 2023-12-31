import re

from proglangs.langlist import ProgrammingLanguage

HIGHLIGHTJS = {
    ProgrammingLanguage.C: 'c',
    ProgrammingLanguage.CPP: 'cpp',
    ProgrammingLanguage.JAVA: 'java',
    ProgrammingLanguage.KOTLIN: 'kotlin',
    ProgrammingLanguage.PASCAL: 'delphi',
    ProgrammingLanguage.DELPHI: 'delphi',
    ProgrammingLanguage.PYTHON: 'py',
    ProgrammingLanguage.CSHARP: 'csharp',
    ProgrammingLanguage.SHELL: 'bash',
    ProgrammingLanguage.ASM: 'x86asm',
}


def get_highlightjs_class(lang):
    return HIGHLIGHTJS.get(lang)


ACE = {
    ProgrammingLanguage.C: 'c_cpp',
    ProgrammingLanguage.CPP: 'c_cpp',
    ProgrammingLanguage.JAVA: 'java',
    ProgrammingLanguage.KOTLIN: 'kotlin',
    ProgrammingLanguage.PASCAL: 'pascal',
    ProgrammingLanguage.DELPHI: 'pascal',
    ProgrammingLanguage.PYTHON: 'python',
    ProgrammingLanguage.CSHARP: 'csharp',
    ProgrammingLanguage.SHELL: 'sh',
    ProgrammingLanguage.ASM: 'assembly_x86',
}


def get_ace_mode(lang):
    return ACE.get(lang, 'text')


PYGMENTS = {
    ProgrammingLanguage.ASM: 'nasm',
    ProgrammingLanguage.KOTLIN: 'kotlin',
    ProgrammingLanguage.CSHARP: 'csharp',
    ProgrammingLanguage.SHELL: 'bash',
}


def get_pygments_lexer(lang):
    return PYGMENTS.get(lang, lang)


FILENAME_EXTENSIONS = {
    ProgrammingLanguage.C: 'c',
    ProgrammingLanguage.CPP: 'cpp',
    ProgrammingLanguage.JAVA: 'java',
    ProgrammingLanguage.KOTLIN: 'kt',
    ProgrammingLanguage.PASCAL: 'pas',
    ProgrammingLanguage.DELPHI: 'dpr',
    ProgrammingLanguage.PYTHON: 'py',
    ProgrammingLanguage.CSHARP: 'cs',
    ProgrammingLanguage.SHELL: 'sh',
    ProgrammingLanguage.ASM: 'asm',
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

    if lang == ProgrammingLanguage.JAVA:
        public_class = _extract_java_public_class(text)
        if public_class is not None:
            name = public_class

    elif lang == ProgrammingLanguage.CSHARP:
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

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

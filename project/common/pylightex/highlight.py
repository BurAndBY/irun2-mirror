import cgi
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound


def do_highlight(code, language):
    try:
        lexer = get_lexer_by_name(language)
    except ClassNotFound:
        lexer = get_lexer_by_name('text')  # Null lexer, does not highlight anything

    formatter = HtmlFormatter(nowrap=True)
    return highlight(code, lexer, formatter)


def do_highlight_trivial(code, language):
    return cgi.escape(code)


def get_highlight_func(pygmentize):
    return do_highlight if pygmentize else do_highlight_trivial

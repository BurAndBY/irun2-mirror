# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import cgi
import itertools
from .highlight import get_highlight_func
from lark import Lark, Transformer, v_args, UnexpectedInput

TEX_GRAMMAR = r'''
// General
_COMMENT: "%" /[^\n]/*
_PARAGRAPH_BREAKER: /\n{2,}/
NEWLINE: /\n/

// Plain text
!usual_symbol: /[^\\%${}~\n\-<>]+/
!unusual_symbol: "<" | ">" | "-"
!special_symbol: "~" | "<<" | ">>" | "--" | "---" | "{}"
!escaped_symbol: "\\" /[\\%${}]/
_plain_text: usual_symbol | unusual_symbol | special_symbol | escaped_symbol

// Math
MATH_SPECIAL: "\\$" | "\\\\"
math_symbol: /[^$]/ | MATH_SPECIAL
equation: math_symbol+
inline_math: "$" equation "$"
display_math: "$$" equation "$$"

// Verbatim
VERBATIM_CHAR: /./s
!inline_verbatim_block: (/[^{}]+/ | ("{" inline_verbatim_block? "}")) inline_verbatim_block?
verbatim_content: VERBATIM_CHAR*
verb_cmd: ("\\verb{" inline_verbatim_block "}") | ("\\verb|" /[^|]+/ "|") | ("\\verb!" /[^!]+/ "!")
path_cmd: "\\path{" inline_verbatim_block "}"
mintinline_cmd: "\\mintinline{" CNAME "}{" inline_verbatim_block "}"
verbatim_env: "\\begin{verbatim}" verbatim_content "\\end{verbatim}"
minted_env: "\\begin{minted}{" CNAME "}" verbatim_content "\\end{minted}"

// Style
texttt_cmd: "\\texttt{" phrase "}"
textit_cmd: "\\textit{" phrase "}"
textbf_cmd: "\\textbf{" phrase "}"
emph_cmd: "\\emph{" phrase "}"
_text_style_cmd: texttt_cmd | textit_cmd | textbf_cmd | emph_cmd

// Document structure
_phrasing_element: _COMMENT | _plain_text | inline_math | verb_cmd | path_cmd | mintinline_cmd | _text_style_cmd

phrase: _phrasing_element*
paragraph: (_phrasing_element | NEWLINE | display_math | verbatim_env | minted_env)+

paragraphs: (_PARAGRAPH_BREAKER? paragraph (_PARAGRAPH_BREAKER paragraph)* _PARAGRAPH_BREAKER?) // at least one paragraph
    | _PARAGRAPH_BREAKER? // no paragraphs

document: paragraphs

%import common.CNAME
'''

CHARACTER_MAP = {
    '~': '\u00A0',
    '<<': '\u00AB',
    '>>': '\u00BB',
    '--': '\u2013',
    '---': '\u2014',
    '{}': '',
}


class TreeToHtml(Transformer):
    def __init__(self, highlight_func):
        self._highlight_func = highlight_func

    def plain_text(self, children):
        return ''.join(children)

    @v_args(inline=True)
    def escaped_symbol(self, backslash, symbol):
        assert backslash == '\\'
        return symbol

    @v_args(inline=True)
    def usual_symbol(self, symbol):
        return symbol

    @v_args(inline=True)
    def unusual_symbol(self, symbol):
        return cgi.escape(symbol)

    def paragraph(self, children):
        return ['<div class="paragraph">'] + children + ['</div>']

    def paragraphs(self, children):
        return list(itertools.chain.from_iterable(children))

    def phrase(self, children):
        return ''.join(children)

    @v_args(inline=True)
    def document(self, paragraphs):
        return ''.join(paragraphs)

    @v_args(inline=True)
    def math_symbol(self, symbol):
        return cgi.escape(symbol)

    def equation(self, children):
        return ''.join(children)

    @v_args(inline=True)
    def inline_math(self, equation):
        return '<span class="math">{}</span>'.format(equation)

    @v_args(inline=True)
    def display_math(self, equation):
        return '<div class="math">{}</div>'.format(equation)

    def inline_verbatim_block(self, children):
        return ''.join(children)

    @v_args(inline=True)
    def verb_cmd(self, block):
        return '<span class="verbatim">{}</span>'.format(cgi.escape(block))

    @v_args(inline=True)
    def path_cmd(self, block):
        return '<span class="path">{}</span>'.format(cgi.escape(block))

    @v_args(inline=True)
    def mintinline_cmd(self, language, block):
        return '<span class="verbatim">{}</span>'.format(self._highlight_func(block, language).rstrip('\n'))

    def verbatim_content(self, children):
        if len(children) > 0 and children[0] == '\n':
            children = children[1:]
        return ''.join(children)

    @v_args(inline=True)
    def verbatim_env(self, content):
        return '<div class="verbatim">{}</div>'.format(cgi.escape(content))

    @v_args(inline=True)
    def minted_env(self, language, content):
        return '<div class="verbatim">{}</div>'.format(self._highlight_func(content, language))

    @v_args(inline=True)
    def special_symbol(self, value):
        return CHARACTER_MAP[value]

    def texttt_cmd(self, children):
        return '<span class="monospace">{}</span>'.format(''.join(children))

    def textit_cmd(self, children):
        return '<i>{}</i>'.format(''.join(children))

    def textbf_cmd(self, children):
        return '<b>{}</b>'.format(''.join(children))

    def emph_cmd(self, children):
        return '<em>{}</em>'.format(''.join(children))


DEBUG = True
PARSER = 'lalr'
TEX_PARSER = Lark(TEX_GRAMMAR, parser=PARSER, debug=DEBUG, start='document')
TEX_PARSER_INLINE = Lark(TEX_GRAMMAR, parser=PARSER, debug=DEBUG, start='phrase')


def _make_error_page(tex, u):
    body = '{}: {}'.format(type(u).__name__, str(u))
    return '<pre class="error">{}</pre>'.format(cgi.escape(body))


def tex2html(tex, inline=False, pygmentize=True, wrap=True):
    parser = TEX_PARSER_INLINE if inline else TEX_PARSER
    try:
        tree = parser.parse(tex)
    except UnexpectedInput as u:
        return _make_error_page(tex, u)

    transformer = TreeToHtml(get_highlight_func(pygmentize))
    html = transformer.transform(tree)

    if not wrap:
        return html
    else:
        return '<{0} class="pylightex">{1}</{0}>'.format('span' if inline else 'div', html)

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

from django import template
from django.utils.html import mark_safe

from common.highlight import get_highlight_style

register = template.Library()


@register.simple_tag(takes_context=True)
def irunner_sourcecode_css(context):
    style = get_highlight_style(context.request)
    formatter = HtmlFormatter(style=style)
    styles = formatter.get_style_defs('.ir-pygments .code pre')

    return mark_safe('<style type="text/css">{0}</style>'.format(styles))


@register.simple_tag(takes_context=False)
def irunner_sourcecode(code, language, hrefs=False):
    if code is None:
        return ''

    try:
        lexer = get_lexer_by_name(language)
    except ClassNotFound:
        lexer = get_lexer_by_name('text')  # Null lexer, does not highlight anything

    if hrefs:
        formatter = HtmlFormatter(linenos='table', lineanchors='line', anchorlinenos=True)
    else:
        formatter = HtmlFormatter(linenos='table')

    result = highlight(code, lexer, formatter)

    return mark_safe('<div class="ir-pygments codehilite">{0}</div>'.format(result))

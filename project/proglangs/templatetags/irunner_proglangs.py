from django import template
from django.utils.html import format_html

from proglangs.models import Compiler
from proglangs.langlist import get_language_label

register = template.Library()


@register.inclusion_tag('proglangs/irunner_proglangs_compilerbox_tag.html')
def irunner_proglangs_compilerbox(compiler, tooltip=False):
    return {
        'compiler': compiler,
        'tooltip': tooltip,
    }


@register.inclusion_tag('proglangs/irunner_proglangs_commandlines_tag.html')
def irunner_proglangs_commandlines(compilers, expanded=False):
    '''
    args:
        compilers: list of Compiler with CompilerDetails selected or a single Compiler
    '''
    return {
        'compilers': [compilers] if isinstance(compilers, Compiler) else compilers,
        'expanded': expanded
    }


@register.simple_tag()
def irunner_proglangs_langbox(language):
    return format_html(
        '<div class="ir-box ir-langbox ir-langbox-{}"><span>{}</span></div>',
        language,
        get_language_label(language)
    )

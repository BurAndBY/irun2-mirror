from django import template

from proglangs.models import Compiler

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

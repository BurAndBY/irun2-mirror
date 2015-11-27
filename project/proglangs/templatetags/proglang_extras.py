from django import template
from proglangs.models import Compiler

register = template.Library()


@register.inclusion_tag('proglangs/extras.html')
def langbox(compiler):
    return {
        'compiler': compiler,
    }


@register.inclusion_tag('proglangs/extras.html')
def langboxbyid(compiler_id, suggest=True):
    compiler = Compiler.objects.filter(pk=compiler_id).first()
    return {
        'compiler': compiler,
        'suggest': suggest,
    }

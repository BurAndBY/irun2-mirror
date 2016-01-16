from django import template

register = template.Library()


@register.inclusion_tag('proglangs/irunner_proglangs_compilerbox_tag.html')
def irunner_proglangs_compilerbox(compiler, tooltip=False):
    return {
        'compiler': compiler,
        'tooltip': tooltip,
    }

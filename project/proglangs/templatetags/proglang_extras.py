from django import template

register = template.Library()


@register.inclusion_tag('proglangs/extras.html')
def langbox(compiler, tooltip=False):
    return {
        'compiler': compiler,
        'tooltip': tooltip,
    }

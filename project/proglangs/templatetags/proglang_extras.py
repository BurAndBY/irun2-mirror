from django import template
register = template.Library()


@register.inclusion_tag('proglangs/extras.html')
def langbox(lang):
    return {
        'lang': lang,
    }

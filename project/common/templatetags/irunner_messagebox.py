from django import template

register = template.Library()


@register.inclusion_tag('common/irunner_messagebox_tag.html')
def irunner_messagebox(style):
    return {'style': style}


@register.inclusion_tag('common/irunner_endmessagebox_tag.html')
def irunner_endmessagebox():
    return {}

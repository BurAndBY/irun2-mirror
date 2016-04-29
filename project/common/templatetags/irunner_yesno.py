from django import template

register = template.Library()


@register.simple_tag(takes_context=False)
def irunner_yesno(value):
    if value is True:
        return '<span class="glyphicon glyphicon-ok text-success"></span>'
    if value is False:
        return '<span class="glyphicon glyphicon-remove text-danger"></span>'
    return ''

from django import template
from django.utils.html import mark_safe

register = template.Library()


@register.simple_tag(takes_context=False)
def irunner_yesno(value):
    if value is True:
        return mark_safe('<span class="glyphicon glyphicon-ok text-success"></span>')
    if value is False:
        return mark_safe('<span class="glyphicon glyphicon-remove text-danger"></span>')
    return mark_safe('&mdash;')

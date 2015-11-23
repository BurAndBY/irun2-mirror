from django import template

register = template.Library()


@register.simple_tag
def system_short_name():
    return 'iRunner 2'


@register.simple_tag
def system_full_name():
    return 'Insight Runner 2'

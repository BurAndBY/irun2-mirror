from django import template

register = template.Library()


@register.inclusion_tag('common/irunner_katex_head.html')
def irunner_katex_head():
    return {}


@register.inclusion_tag('common/irunner_katex_body.html')
def irunner_katex_body():
    return {}

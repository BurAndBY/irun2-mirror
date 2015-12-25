from django import template

register = template.Library()


@register.inclusion_tag('problems/complexitybox_tag.html')
def complexitybox(complexity):
    return {'complexity': complexity}

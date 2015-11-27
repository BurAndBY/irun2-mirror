from django import template
register = template.Library()


@register.inclusion_tag('problems/problemstatement_tag.html')
def problemstatement(statement):
    return {'statement': statement}

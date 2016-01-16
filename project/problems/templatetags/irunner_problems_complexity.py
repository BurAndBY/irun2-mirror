from django import template

register = template.Library()


@register.inclusion_tag('problems/irunner_problems_complexity_tag.html')
def irunner_problems_complexity(complexity):
    return {'complexity': complexity}

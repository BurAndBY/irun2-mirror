from django import template

register = template.Library()


@register.inclusion_tag('common/irunner_mass_hidden_tag.html')
def irunner_mass_hidden(ids, next=None):
    return {'ids': ids, 'next': next}

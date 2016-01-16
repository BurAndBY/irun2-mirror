from django import template

register = template.Library()


@register.inclusion_tag('common/irunner_pagination_tag.html')
def irunner_pagination(pagination_context):
    return {'ctxt': pagination_context}

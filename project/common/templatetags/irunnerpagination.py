from django import template

register = template.Library()


@register.inclusion_tag('common/irunnerpagination_tag.html')
def irunnerpagination(pagination_context):
    return {'ctxt': pagination_context}

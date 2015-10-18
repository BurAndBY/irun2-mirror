from django import template
register = template.Library()


@register.inclusion_tag('storage/extras.html')
def show_resource(representation):
    return {'representation': representation}

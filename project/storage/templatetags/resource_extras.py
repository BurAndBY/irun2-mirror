from django import template
register = template.Library()


@register.inclusion_tag('storage/extras.html')
def show_resource(representation, programming_language=None):
    return {
        'representation': representation,
        'programming_language': programming_language
    }

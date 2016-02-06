from django import template
register = template.Library()


@register.inclusion_tag('storage/irunner_storage_show_tag.html')
def irunner_storage_show(representation, programming_language=None):
    return {
        'representation': representation,
        'programming_language': programming_language
    }


@register.inclusion_tag('storage/irunner_storage_showbrief_tag.html')
def irunner_storage_showbrief(representation):
    return {
        'representation': representation,
    }

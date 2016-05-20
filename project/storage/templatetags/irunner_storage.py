from django import template

from proglangs.utils import get_highlightjs_class

register = template.Library()


@register.inclusion_tag('storage/irunner_storage_show_tag.html')
def irunner_storage_show(representation, programming_language=None, compact=False):
    return {
        'representation': representation,
        'programming_language': programming_language,
        'compact': compact,
    }


@register.inclusion_tag('storage/irunner_storage_showbrief_tag.html')
def irunner_storage_showbrief(representation):
    return {
        'representation': representation,
    }


@register.inclusion_tag('storage/irunner_storage_showcode_tag.html')
def irunner_storage_showcode(representation, compiler, hrefs=False):
    language = get_highlightjs_class(compiler.language)
    return {
        'representation': representation,
        'language': language,
        'hrefs': hrefs,
    }

from django import template
from django.utils.html import mark_safe
from django.utils.html import format_html

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


@register.simple_tag(takes_context=False)
def irunner_storage_hex(hexdata, compact=False):
    result = []
    for line in hexdata:
        if compact:
            portion = format_html(
                '<span class="text-muted">{}  {}</span>',
                line.hex1, line.hex2
            )
        else:
            portion = format_html(
                '<span class="text-info">{}</span>:  '
                '<span class="text-muted">{}  {}</span>  '
                '<span class="text-primary">{}</span>',
                line.offset, line.hex1, line.hex2, line.ascii
            )
        result.append(portion)

    return mark_safe('\n'.join(result))

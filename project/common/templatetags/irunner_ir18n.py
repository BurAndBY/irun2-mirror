from django import template

register = template.Library()


@register.inclusion_tag('common/ir18n/widget_row.html')
def ir18n_row(allowed_langs, language, value):
    return {
        'allowed_langs': allowed_langs,
        'language': language,
        'value': value,
    }

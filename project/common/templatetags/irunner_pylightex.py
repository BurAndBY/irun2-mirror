from django import template
from django.utils.html import mark_safe

from pygments.formatters import HtmlFormatter

register = template.Library()


@register.inclusion_tag('common/irunner_pylightex_head.html')
def irunner_pylightex_head():
    formatter = HtmlFormatter(style='default')
    styles = formatter.get_style_defs('.pylightex .verbatim')
    styles = styles.replace('background: #f8f8f8;', '')
    return {'styles': styles}


@register.inclusion_tag('common/irunner_pylightex_body.html')
def irunner_pylightex_body():
    return {}


@register.filter(name='stylizetex')
def stylizetex(value):
    return mark_safe(value.replace(
        'TeX', 'T<span style="'
        'text-transform: uppercase; '
        'vertical-align: -0.5ex; '
        'margin-left: -0.1667em; '
        'margin-right: -0.125em; '
        'line-height: 1ex;">e</span>X'))

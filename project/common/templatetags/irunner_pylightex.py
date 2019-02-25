from django import template

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

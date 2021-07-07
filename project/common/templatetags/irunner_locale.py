from django import template

from common.locale.selector import LanguageSelector

register = template.Library()


@register.inclusion_tag('common/irunner_locale_selector_tag.html')
def irunner_locale_selector(selector):
    if not isinstance(selector, LanguageSelector):
        raise TypeError('invalid argument')

    return {'selector': selector}

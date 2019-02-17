from django import template
from django.conf import settings
from django.utils import translation

register = template.Library()


@register.inclusion_tag('home/irunner_home_block_tag.html')
def irunner_home_block(block):
    return {'block': block}


@register.inclusion_tag('home/irunner_home_logo_tag.html')
def irunner_home_main_logo():
    try:
        conf = settings.MAIN_LOGO
    except AttributeError:
        conf = {}

    lang = translation.get_language()

    # English by default
    logo = conf.get(lang, conf.get('en', {}))

    return {'logo': logo}

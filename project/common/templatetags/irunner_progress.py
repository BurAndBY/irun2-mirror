import uuid

from django import template
from django.utils.encoding import smart_text

register = template.Library()


@register.inclusion_tag('common/irunner_progress_tag.html')
def irunner_progress(url, value=0, value_good=0, value_bad=0, total=0, active=None):
    context = {}

    def _set(x, suffix):
        if x > 0:
            percent = (100. * x / total) if total > 0 else 0.
            context['style' + suffix] = 'width: {0}%'.format(percent)
            context['value' + suffix] = x
        else:
            context['style' + suffix] = 'width: 0'
            context['value' + suffix] = ''

    _set(value, '')
    _set(value_good, '_good')
    _set(value_bad, '_bad')

    context['url'] = url
    context['refresh'] = True
    context['active'] = active if active is not None else (value + value_good + value_bad < total)
    context['uid'] = smart_text(uuid.uuid1().hex)
    return context

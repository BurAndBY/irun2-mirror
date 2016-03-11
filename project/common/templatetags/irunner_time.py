from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

register = template.Library()


@register.simple_tag(takes_context=False)
def irunner_time_deltaseconds(t1, t2):
    if t1 is not None and t2 is not None:
        return u'{0:.1f} {1}'.format((t2 - t1).total_seconds(), _('s'))
    else:
        return mark_safe('&mdash;')


DATETIME_FORMAT = '%Y-%m-%d %H:%M'


@register.simple_tag(takes_context=False)
def irunner_time_datetime(dt):
    return dt.strftime(DATETIME_FORMAT)

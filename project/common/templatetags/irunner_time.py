from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext

register = template.Library()


@register.simple_tag(takes_context=False)
def irunner_time_deltaseconds(t1, t2):
    if t1 is not None and t2 is not None:
        return u'{0} {1}'.format((t2 - t1).total_seconds(), _('s'))
    else:
        return mark_safe('&mdash;')


DATETIME_FORMAT = '%Y-%m-%d %H:%M'


@register.simple_tag(takes_context=False)
def irunner_time_datetime(dt):
    return dt.strftime(DATETIME_FORMAT)


@register.simple_tag(takes_context=False)
def irunner_time_deltahms(dt):
    hours, remainder = divmod(dt.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    hms = u'{0}:{1:02d}:{2:02d}'.format(hours, minutes, seconds)
    if dt.days == 0:
        return hms
    else:
        days = ungettext('%(count)d day', '%(count)d days', abs(dt.days)) % {'count': dt.days}
        return u'{0}, {1}'.format(days, hms)

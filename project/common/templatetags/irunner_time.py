from __future__ import unicode_literals

from django import template
from django.utils.html import avoid_wrapping
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.utils.translation import pgettext, ungettext, ungettext_lazy

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


def _hms_string(dt):
    '''
    dt: datetime.timedelta
    '''
    hours, remainder = divmod(dt.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    hms = u'{0}:{1:02d}:{2:02d}'.format(hours, minutes, seconds)
    if dt.days == 0:
        return hms
    else:
        days = ungettext('%(count)d day', '%(count)d days', abs(dt.days)) % {'count': dt.days}
        return u'{0}, {1}'.format(days, hms)


CHUNKS = (
    (60 * 60 * 24, ungettext_lazy('%d day', '%d days')),
    (60 * 60, ungettext_lazy('%d hour', '%d hours')),
    (60, ungettext_lazy('%d minute', '%d minutes')),
    (1, ungettext_lazy('%d second', '%d seconds')),
)


def _humanized_string(delta):
    '''
    delta: datetime.timedelta
    '''
    # ignore microseconds
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        _, name = CHUNKS[-1]
        return avoid_wrapping(name % 0)

    for i, (seconds, name) in enumerate(CHUNKS):
        count = since // seconds
        if count != 0:
            break
    result = avoid_wrapping(name % count)
    if i + 1 < len(CHUNKS):
        # Now get the second item
        seconds2, name2 = CHUNKS[i + 1]
        count2 = (since - (seconds * count)) // seconds2
        if count2 != 0:
            result += pgettext('time', ', ') + avoid_wrapping(name2 % count2)
    return result


def _calc_delta(start, finish):
    return finish - start


@register.simple_tag
def irunner_time_deltahms(dt):
    '''
    Deprecated: use irunner_timedelta_hms() instead.
    '''
    return _hms_string(dt)


@register.simple_tag
def irunner_timedelta_hms(dt):
    return _hms_string(dt)


@register.simple_tag
def irunner_timedelta_humanized(dt):
    return _humanized_string(dt)


@register.simple_tag
def irunner_timediff_hms(start, finish):
    return _hms_string(_calc_delta(start, finish))


@register.simple_tag
def irunner_timediff_humanized(start, finish):
    return _humanized_string(_calc_delta(start, finish))

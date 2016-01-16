from django import template

register = template.Library()


def _prepare(actual, limit, preparer):
    if limit:
        clamped = min(max(0, actual), limit)
        percent = int(round(100.0 * clamped / limit))
    else:
        percent = 0

    return {
        'actual': preparer(actual),
        'limit': preparer(limit),
        'percent': percent,
    }


@register.inclusion_tag('solutions/timelimitbox.html')
def timelimitbox(actual, limit):
    return _prepare(actual, limit, lambda x: x * 0.001)


@register.inclusion_tag('solutions/memorylimitbox.html')
def memorylimitbox(actual, limit):
    return _prepare(actual, limit, lambda x: x // 1024)

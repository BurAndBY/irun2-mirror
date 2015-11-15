# -*- coding: utf-8 -*-

from django import template
from solutions.models import Judgement, Outcome

register = template.Library()

TWO_LETTER_CODES = {
    Outcome.ACCEPTED: 'AC',
    Outcome.COMPILATION_ERROR: 'CE',
    Outcome.WRONG_ANSWER: 'WA',
    Outcome.TIME_LIMIT_EXCEEDED: 'TL',
    Outcome.MEMORY_LIMIT_EXCEEDED: 'ML',
    Outcome.IDLENESS_LIMIT_EXCEEDED: 'IL',
    Outcome.RUNTIME_ERROR: 'RE',
    Outcome.PRESENTATION_ERROR: 'PE',
    Outcome.SECURITY_VIOLATION: 'SV',
    Outcome.CHECK_FAILED: 'CF'
}


def _get_style(outcome, code):
    if outcome == Outcome.ACCEPTED:
        return 'ok'
    elif code is not None:
        return 'fail'
    else:
        return ''


@register.inclusion_tag('solutions/extras.html')
def judgementbox(judgement):
    if judgement is not None and judgement.status == Judgement.DONE:
        code = TWO_LETTER_CODES.get(judgement.outcome)
        return {
            'code': code,
            'style': _get_style(judgement.outcome, code),
            'test_no': judgement.test_number
        }
    else:
        return {
            'code': '…' if judgement is not None else '—',
            'style': '',
            'test_no': 0
        }


@register.inclusion_tag('solutions/extras.html')
def outcomebox(outcome):
    ctx = {}
    if outcome is not None:
        code = TWO_LETTER_CODES.get(outcome)
        ctx = {
            'code': code,
            'style': _get_style(outcome, code)
        }
    return ctx

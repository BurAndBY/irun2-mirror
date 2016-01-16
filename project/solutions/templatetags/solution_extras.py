# -*- coding: utf-8 -*-

import uuid

from django import template
from solutions.models import Judgement, Outcome
from solutions.permissions import SolutionPermissions


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
def judgementbox(judgement, header=False):
    if judgement is not None and judgement.status == Judgement.DONE:
        code = TWO_LETTER_CODES.get(judgement.outcome)
        return {
            'code': code,
            'style': _get_style(judgement.outcome, code),
            'test_no': judgement.test_number,
            'header': header
        }
    else:
        return {
            'code': '…' if judgement is not None else '—',
            'style': '',
            'test_no': 0,
            'header': header
        }


@register.inclusion_tag('solutions/extras.html')
def irunner_solutions_outcomebox(outcome):
    '''
    Displays outcome for a single test.

    args:
        outcome(int): value of solutions.models.Outcome enum
    '''
    ctx = {}
    if outcome is not None:
        code = TWO_LETTER_CODES.get(outcome)
        ctx = {
            'code': code,
            'style': _get_style(outcome, code)
        }
    return ctx


@register.inclusion_tag('solutions/irunner_testresults_tag.html')
def irunner_testresults(test_results, solution_permissions, url_pattern=None, first_placeholder=None):
    '''
    Displays a table with results per tests.
    '''
    if not isinstance(solution_permissions, SolutionPermissions):
        raise TypeError('SolutionPermissions required')

    uid = unicode(uuid.uuid1().hex)

    enable_tests_data = solution_permissions.tests_data and url_pattern

    return {
        'test_results': test_results,
        'solution_permissions': solution_permissions,
        'url_pattern': url_pattern,
        'first_placeholder': first_placeholder,
        'uid': uid,
        'enable_tests_data': enable_tests_data,
    }

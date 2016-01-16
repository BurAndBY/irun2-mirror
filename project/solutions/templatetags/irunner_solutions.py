# -*- coding: utf-8 -*-

import uuid

from django import template

from solutions.models import Judgement, Outcome
from solutions.permissions import SolutionPermissions


register = template.Library()

TWO_LETTER_OUTCOME_CODES = {
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

ONE_LETTER_STATUS_CODES = {
    Judgement.COMPILING: 'C',
    Judgement.TESTING: 'T',
}


def _get_style(outcome, code):
    if outcome == Outcome.ACCEPTED:
        return 'ok'
    elif code is not None:
        return 'fail'
    else:
        return ''


@register.inclusion_tag('solutions/irunner_solutions_box_tag.html')
def irunner_solutions_judgementbox(judgement, tooltip=True):
    '''
    Displays judgement state.

    args:
        judgement(solutions.models.Judgement)
        tooltip: show hint (localized explanation) in tooltip
    '''
    context = {
        'code': '—',
        'style': '',
        'test_no': 0,
        'tooltip': judgement.show_status() if (tooltip and (judgement is not None)) else '',
    }

    if judgement is not None:
        if judgement.status == Judgement.DONE:
            code = TWO_LETTER_OUTCOME_CODES.get(judgement.outcome)
            context['code'] = code
            context['style'] = _get_style(judgement.outcome, code)
            context['test_no'] = judgement.test_number
        else:
            context['code'] = ONE_LETTER_STATUS_CODES.get(judgement.status, u'…')
            context['test_no'] = judgement.test_number
    return context


@register.inclusion_tag('solutions/irunner_solutions_box_tag.html')
def irunner_solutions_outcomebox(outcome):
    '''
    Displays outcome for a single test.

    args:
        outcome(int): value of solutions.models.Outcome enum
    '''
    context = {}
    if outcome is not None:
        code = TWO_LETTER_OUTCOME_CODES.get(outcome)
        context = {
            'code': code,
            'style': _get_style(outcome, code),
        }
    return context


@register.inclusion_tag('solutions/irunner_solutions_testresults_tag.html')
def irunner_solutions_testresults(test_results, solution_permissions, url_pattern=None, first_placeholder=None):
    '''
    Displays a table with results per test.
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


def _prepare_limit(actual, limit, preparer):
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


@register.inclusion_tag('solutions/irunner_solutions_timelimitbox_tag.html')
def irunner_solutions_timelimitbox(actual, limit):
    return _prepare_limit(actual, limit, lambda x: x * 0.001)


@register.inclusion_tag('solutions/irunner_solutions_memorylimitbox_tag.html')
def irunner_solutions_memorylimitbox(actual, limit):
    return _prepare_limit(actual, limit, lambda x: x // 1024)


@register.inclusion_tag('solutions/irunner_solutions_livesubmission_tag.html')
def irunner_solutions_livesubmission(solution_id):
    assert solution_id is not None
    return {
        'solution_id': solution_id,
        'uid': uuid.uuid1().hex,
    }

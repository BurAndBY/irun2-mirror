# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import uuid

from django import template
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from common.outcome import Outcome
from solutions.models import Judgement
from solutions.permissions import SolutionPermissions


register = template.Library()

TWO_LETTER_OUTCOME_CODES = {
    Outcome.ACCEPTED: 'OK',
    Outcome.COMPILATION_ERROR: 'CE',
    Outcome.WRONG_ANSWER: 'WA',
    Outcome.TIME_LIMIT_EXCEEDED: 'TLE',
    Outcome.MEMORY_LIMIT_EXCEEDED: 'MLE',
    Outcome.IDLENESS_LIMIT_EXCEEDED: 'ILE',
    Outcome.RUNTIME_ERROR: 'RTE',
    Outcome.PRESENTATION_ERROR: 'PE',
    Outcome.SECURITY_VIOLATION: 'SV',
    Outcome.CHECK_FAILED: 'CF'
}

ONE_LETTER_STATUS_CODES = {
    Judgement.COMPILING: 'C',
    Judgement.TESTING: 'T',
}

ELLIPSIS = '…'


def _get_style(outcome, code):
    if outcome == Outcome.ACCEPTED:
        return 'ok' if not settings.APRIL_FOOLS_DAY_MODE else 'fail'
    elif code not in (None, ELLIPSIS):
        return 'fail' if not settings.APRIL_FOOLS_DAY_MODE else 'ok'
    else:
        return ''


@register.inclusion_tag('solutions/irunner_solutions_box_tag.html')
def irunner_solutions_judgementbox(judgement, tooltip=False, complete=True):
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
        'tooltip': '',
    }

    if judgement is not None:
        if judgement.status == Judgement.DONE:
            if complete or (judgement.sample_tests_passed is False):
                code = TWO_LETTER_OUTCOME_CODES.get(judgement.outcome)
                context['code'] = code
                context['style'] = _get_style(judgement.outcome, code)
                context['test_no'] = judgement.test_number
            else:
                context['code'] = 'AC'
                context['style'] = 'pending'
        else:
            context['code'] = ONE_LETTER_STATUS_CODES.get(judgement.status, ELLIPSIS)
            if complete:
                context['test_no'] = judgement.test_number

    if tooltip:
        context['tooltip'] = judgement.show_status(complete)

    return context


@register.simple_tag(takes_context=False)
def irunner_solutions_judgementtext(judgement, complete=True):
    '''
    Displays judgement state as text (i. e. "Wrong Answer (42)").
    '''
    text = ''
    if judgement is not None:
        text = judgement.show_status(complete)

    return text


def _find_in_choices(choices, what):
    for pair in choices:
        if pair[0] == what:
            return pair[1]
    return ''


@register.inclusion_tag('solutions/irunner_solutions_box_tag.html')
def irunner_solutions_outcomebox(outcome, tooltip=False):
    '''
    Displays outcome for a single test.

    args:
        outcome(int): value of solutions.models.Outcome enum
    '''
    context = {}
    if outcome is not None:
        code = TWO_LETTER_OUTCOME_CODES.get(outcome, ELLIPSIS)
        context = {
            'code': code,
            'style': _get_style(outcome, code),
            'tooltip': _find_in_choices(Outcome.CHOICES, outcome) if tooltip else '',
        }
    return context


@register.simple_tag(takes_context=False)
def irunner_solutions_scorebox(judgement=None, hide_score_if_accepted=False):
    '''
    Displays score for a judgement.

    args:
        judgement
    '''

    classes = ['ir-box', 'ir-scorebox']
    contents = '&mdash;'

    if judgement is not None:
        accepted = (judgement.outcome == Outcome.ACCEPTED)

        if accepted:
            classes.append('ir-scorebox-accepted')
        else:
            classes.append('ir-scorebox-attempted')

        if accepted and hide_score_if_accepted:
            contents = '&nbsp;'
        else:
            if judgement.score == judgement.max_score:
                contents = '{0}'.format(judgement.score)
            else:
                contents = '{0}&thinsp;/&thinsp;{1}'.format(judgement.score, judgement.max_score)

    return '<div class="{0}">{1}</div>'.format(' '.join(classes), contents)


@register.inclusion_tag('solutions/irunner_solutions_testresults_tag.html')
def irunner_solutions_testresults(test_results, solution_permissions, url_pattern=None, first_placeholder=None):
    '''
    Displays a table with results per test.
    '''
    if not isinstance(solution_permissions, SolutionPermissions):
        raise TypeError('SolutionPermissions required')

    uid = unicode(uuid.uuid1().hex)

    any_toggleable = False

    pairs = []
    for test in test_results:
        toggleable = (url_pattern is not None) and (solution_permissions.tests_data or test.is_sample)
        any_toggleable |= toggleable
        pairs.append((test, toggleable))

    return {
        'test_results': pairs,
        'solution_permissions': solution_permissions,
        'url_pattern': url_pattern,
        'first_placeholder': first_placeholder,
        'uid': uid,
        'any_toggleable': any_toggleable,
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
        'red_style': 'danger' if not settings.APRIL_FOOLS_DAY_MODE else 'success',
        'green_style': 'success' if not settings.APRIL_FOOLS_DAY_MODE else 'danger',
    }


@register.inclusion_tag('solutions/irunner_solutions_rejudgestate_tag.html')
def irunner_solutions_rejudgestate(committed):
    return {'committed': committed}


GENERAL_FAILURE_MESSAGES = {
    'UNKNOWN': _('unknown error'),
    'CHECKER_NOT_COMPILED': _('error while compiling checker'),
    'VALIDATOR_NOT_COMPILED': _('error while compiling validator'),
    'UNKNOWN_PROGRAMMING_LANGUAGE': _('compiler is not available for the testing module'),
}


@register.inclusion_tag('solutions/irunner_solutions_checkfailed_tag.html')
def irunner_solutions_checkfailed(extra_info):
    context = {}
    if extra_info:
        context['reason'] = GENERAL_FAILURE_MESSAGES.get(extra_info.general_failure_reason, extra_info.general_failure_reason)
        context['message'] = extra_info.general_failure_message
    return context


@register.inclusion_tag('solutions/irunner_solutions_sourcelink_tag.html')
def irunner_solutions_sourcelink(solution):
    return {
        'solution': solution,
    }

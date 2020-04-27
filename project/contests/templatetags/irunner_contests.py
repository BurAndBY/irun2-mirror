from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from common.stringutils import cut_text_block

from contests.models import ContestKind
from contests.services import ContestTiming

register = template.Library()


@register.inclusion_tag('contests/irunner_contests_standings_tag.html')
def irunner_contests_standings(contest_results, my_id=None, user_url=None, show_problem_names=True, show_usernames=False):
    return {
        'results': contest_results,
        'my_id': my_id,
        'user_url': user_url,
        'show_problem_names': show_problem_names,
        'show_usernames': show_usernames,
    }


@register.inclusion_tag('contests/irunner_contests_timing_tag.html')
def irunner_contests_timing(timing, user_url=None):
    ctx = {}
    if timing.get() == ContestTiming.BEFORE:
        ctx['status'] = 'BEFORE'
    elif timing.get() == ContestTiming.IN_PROGRESS:
        ctx['status'] = 'IN_PROGRESS'
    elif timing.get() == ContestTiming.AFTER:
        ctx['status'] = 'AFTER'

    ctx['time_before'] = timing.get_time_before()
    ctx['time_passed'] = timing.get_time_passed()
    ctx['time_total'] = timing.get_time_total()
    return ctx


@register.simple_tag
def irunner_contests_showproblem(resolver, problem_id):
    return resolver.get_problem_name(problem_id)


@register.inclusion_tag('contests/irunner_contests_message_tag.html')
def irunner_contests_message(message, edit_mode=False, contest_id=None):
    return {
        'message': message,
        'edit_mode': edit_mode,
        'contest_id': contest_id,
    }


@register.inclusion_tag('contests/irunner_contests_question_tag.html')
def irunner_contests_question(question, problem_resolver, contest_id=None, url_pattern=None):
    return {
        'question': question,
        'resolver': problem_resolver,
        'contest_id': contest_id,
        'url_pattern': url_pattern,
    }


@register.simple_tag
def irunner_contests_printoutsnippet(text):
    _, text = cut_text_block(text, 10, 80)
    return escape(text)


KINDS = {
    ContestKind.OFFICIAL: (_('Off.'), 'label-success'),
    ContestKind.TRIAL: (_('Trial'), 'label-warning'),
    ContestKind.QUALIFYING: (_('Qual.'), 'label-info'),
    ContestKind.TRAINING: (_('Train.'), 'label-default'),
}


@register.simple_tag
def irunner_contests_kind(kind):
    pair = KINDS.get(kind)
    if pair is None:
        return ''

    short_text, cls = pair
    text = ContestKind.VALUE_TO_STRING.get(kind, '')
    return mark_safe('<span class="label {}" title="{}">{}</span>'.format(cls, text, short_text))


@register.inclusion_tag('contests/irunner_contests_minilist_tag.html')
def irunner_contests_minilist(contests):
    return {
        'contests': contests
    }

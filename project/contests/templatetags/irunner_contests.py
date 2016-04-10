from django import template

from contests.services import ContestTiming

register = template.Library()


@register.inclusion_tag('contests/irunner_contests_standings_tag.html')
def irunner_contests_standings(contest_results, my_id=None, user_url=None):
    return {
        'results': contest_results,
        'my_id': my_id,
        'user_url': user_url,
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

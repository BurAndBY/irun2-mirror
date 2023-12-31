from __future__ import unicode_literals

import uuid

from django import template
from django.conf import settings
from django.urls import reverse
from django.utils.html import format_html, mark_safe, escape

register = template.Library()


@register.inclusion_tag('courses/irunner_courses_criterion_tag.html')
def irunner_courses_criterion(criterion, value, tooltip=False, editable=False):
    return {
        'criterion': criterion,
        'value': value,
        'tooltip': tooltip,
        'editable': editable,
    }


@register.inclusion_tag('courses/irunner_courses_slotresult_tag.html')
def irunner_courses_slotresult(slot_result, course_id, solution_permissions, user_id=None, editable=False):
    return {
        'course_id': course_id,  # for links to problem statements
        'user_id': user_id,  # for links to the list of solutions
        'slot_result': slot_result,
        'problem_result': slot_result.problem_result,
        'editable': editable,
        'solution_permissions': solution_permissions,
        'uid': uuid.uuid1().hex
    }


@register.inclusion_tag('courses/irunner_courses_slotresult_tag.html')
def irunner_courses_problemresult(problem_result, course_id, solution_permissions, user_id=None):
    return {
        'course_id': course_id,  # for links to problem statements
        'user_id': user_id,  # for links to the list of solutions
        'slot_result': None,
        'problem_result': problem_result,
        'editable': False,
        'solution_permissions': solution_permissions,
        'uid': uuid.uuid1().hex
    }


@register.inclusion_tag('courses/irunner_courses_standings_tag.html')
def irunner_courses_standings(course_id, user_cache, user, can_assign_problems, course_descr, results, wide=False):
    return {
        'course_id': course_id,
        'user_cache': user_cache,
        'user': user,
        'can_assign_problems': can_assign_problems,
        'course_descr': course_descr,
        'results': results,
        'wide': wide,
        'hide_score_if_accepted': not wide,
    }


@register.simple_tag
def irunner_courses_showuser(user_id, user_cache):
    return user_cache.get_user(user_id).as_html()


def _make_subgroup_span(subgroup_descr):
    if subgroup_descr is None:
        return ''
    return format_html(
        '<span class="ir-subgroup-badge ir-subgroup-badge-{0}">{1}</span>',
        subgroup_descr.number,
        subgroup_descr.name
    )


def _make_full_name_span(user_descr, last_name_first):
    tokens = []
    if user_descr.first_name:
        tokens.append(escape(user_descr.first_name))
    if user_descr.last_name:
        tokens.append(format_html('<span class="ir-lname">{0}</span>', user_descr.last_name))
    if len(tokens) == 2 and settings.LAST_NAME_FIRST_IN_COURSES and last_name_first:
        tokens[0], tokens[1] = tokens[1], tokens[0]

    # strike out disabled users
    if not user_descr.is_active:
        tokens = ['<s>'] + tokens + ['</s>']

    return mark_safe(' '.join(tokens))


def _make_link_impl(card_url, full_name, cls, href, is_hidden):
    if not is_hidden:
        return format_html(
            '<a class="ir-card-link {0}" role="button" data-poload="{1}"{2}>{3}</a>',
            cls,
            card_url,
            href,
            full_name
        )
    else:
        return format_html(
            '<a class="ir-card-link {0}" role="button"{1}>{2}</a>',
            cls,
            href,
            full_name
        )


def _make_link(card_url, full_name, url, is_hidden):
    if url:
        return _make_link_impl(card_url, full_name, mark_safe('ir-course-user-link'), format_html(' href="{0}"', url), is_hidden)
    else:
        return _make_link_impl(card_url, full_name, mark_safe('ir-course-user-nolink'), mark_safe(''), is_hidden)


@register.simple_tag
def irunner_courses_user_card(user_id, user_cache, last_name_first=False, url=None):
    card_url = reverse('users:card', args=(user_id,))
    user_descr = user_cache.get_user(user_id)
    full_name = _make_full_name_span(user_descr, last_name_first)

    tokens = [_make_link(card_url, full_name, url, user_descr.is_hidden)]
    if user_descr.subgroup is not None:
        tokens.append(_make_subgroup_span(user_descr.subgroup))
    return mark_safe(' '.join(tokens))


@register.simple_tag
def irunner_courses_showsubgroup(subgroup_id, user_cache):
    subgroup = user_cache.get_subgroup(subgroup_id)
    return _make_subgroup_span(subgroup)

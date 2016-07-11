import uuid

from django import template
from django.core.urlresolvers import reverse
from django.utils.html import format_html, mark_safe

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
def irunner_courses_slotresult(slot_result, course_id, user_id=None, editable=False):
    return {
        'course_id': course_id,  # for links to problem statements
        'user_id': user_id,  # for links to the list of solutions
        'slot_result': slot_result,
        'problem_result': slot_result.problem_result,
        'editable': editable,
        'uid': uuid.uuid1().hex
    }


@register.inclusion_tag('courses/irunner_courses_slotresult_tag.html')
def irunner_courses_problemresult(problem_result, course_id, user_id=None):
    return {
        'course_id': course_id,  # for links to problem statements
        'user_id': user_id,  # for links to the list of solutions
        'slot_result': None,
        'problem_result': problem_result,
        'editable': False,
        'uid': uuid.uuid1().hex
    }


@register.simple_tag
def irunner_courses_showuser(user_id, user_cache):
    return user_cache.get_user(user_id).as_html()


@register.simple_tag
def irunner_courses_user_card(user_id, user_cache, last_name_first=False, url=None):
    #return user_cache.get_user(user_id).as_html()
    card_url = reverse('users:card', args=(user_id,))
    user_descr = user_cache.get_user(user_id)

    tokens = []
    if user_descr.first_name:
        tokens.append(user_descr.first_name)
    if user_descr.last_name:
        tokens.append(format_html(u'<span class="ir-lname">{0}</span>', user_descr.last_name))
    if len(tokens) == 2 and last_name_first:
        tokens[0], tokens[1] = tokens[1], tokens[0]
    full_name = mark_safe(u' '.join(tokens))

    subgroup_class = u'ir-subgroup-badge ir-subgroup-badge-{0}'.format(user_descr.subgroup_number)

    subgroup = u''
    if user_descr.subgroup_name:
        subgroup = format_html(u' <span class="{0}">{1}</span>', subgroup_class, user_descr.subgroup_name)

    href = u''
    cls = u'ir-course-user-nolink'
    if url:
        href = format_html(' href="{0}"', url)
        cls = u'ir-course-user-link'

    return format_html(
        u'<a class="ir-card-link {0}" role="button" data-poload="{1}"{2}>{3}</a>{4}',
        cls,
        card_url,
        href,
        full_name,
        subgroup
    )

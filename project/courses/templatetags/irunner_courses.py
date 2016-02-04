import uuid

from django import template

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
def irunner_courses_slotresult(slot_result, course_id, editable=False):
    return {
        'course_id': course_id,  # for links to problem statements
        'slot_result': slot_result,
        'editable': editable,
        'uid': uuid.uuid1().hex
    }

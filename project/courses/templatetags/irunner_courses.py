from django import template

register = template.Library()


@register.inclusion_tag('courses/irunner_courses_criterion_tag.html')
def irunner_courses_criterion(criterion, value, tooltip=False):
    return {
        'criterion': criterion,
        'value': value,
        'tooltip': tooltip
    }

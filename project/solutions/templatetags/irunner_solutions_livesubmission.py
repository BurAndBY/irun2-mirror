import uuid


from django import template

register = template.Library()


@register.inclusion_tag('solutions/irunner_solutions_livesubmission_tag.html')
def irunner_solutions_livesubmission(solution_id):
    return {
        'solution_id': solution_id,
        'uid': uuid.uuid1().hex,
    }

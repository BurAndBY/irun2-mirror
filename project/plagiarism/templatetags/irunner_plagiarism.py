# -*- coding: utf-8 -*-

from django import template
from django.utils.html import mark_safe

register = template.Library()


@register.inclusion_tag('plagiarism/irunner_plagiarism_box_tag.html')
def irunner_plagiarism_box(aggregated_result, solution_id):
    '''
    Displays plagiarism aggregated result.

    args:
        aggregated_result(plagiarism.models.JudgementResult)
    '''
    context = {}
    if aggregated_result:
        context['relevance'] = aggregated_result.relevance
        context['solution_id'] = solution_id
        if aggregated_result.relevance > 0.8:
            context['style'] = 'danger'
        elif aggregated_result.relevance > 0.0:
            context['style'] = 'warning'

    else:
        context['relevance'] = None
    return context


@register.simple_tag(takes_context=False)
def irunner_plagiarism_csscolor(x):
    x = min(max(x, 0.0), 1.0)
    return mark_safe('hsl(0, {0}%, 50%)'.format(round(x * 100)))

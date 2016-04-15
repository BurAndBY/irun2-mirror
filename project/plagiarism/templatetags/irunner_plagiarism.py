# -*- coding: utf-8 -*-

from django import template

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

from django import template

register = template.Library()


@register.inclusion_tag('problems/irunner_problems_complexity_tag.html')
def irunner_problems_complexity(complexity):
    return {'complexity': complexity}


@register.inclusion_tag('problems/irunner_problems_statement_tag.html')
def irunner_problems_statement(statement):
    return {'statement': statement}


@register.inclusion_tag('problems/irunner_problems_list_tag.html')
def irunner_problems_list(problems, pagination_context=None, show_checkbox=False):
    return {
        'problems': problems,
        'pagination_context': pagination_context,
        'show_checkbox': show_checkbox
    }

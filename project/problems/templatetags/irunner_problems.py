from django import template

register = template.Library()


@register.inclusion_tag('problems/irunner_problems_difficulty_tag.html')
def irunner_problems_difficulty(difficulty, used=False):
    return {'difficulty': difficulty, 'used': used}


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


@register.inclusion_tag('problems/irunner_problems_io_tag.html')
def irunner_problems_inputfile(filename):
    if filename:
        return {'filename': filename, 'emph': False}
    else:
        return {'filename': 'stdin', 'emph': True}


@register.inclusion_tag('problems/irunner_problems_io_tag.html')
def irunner_problems_outputfile(filename):
    if filename:
        return {'filename': filename, 'emph': False}
    else:
        return {'filename': 'stdout', 'emph': True}

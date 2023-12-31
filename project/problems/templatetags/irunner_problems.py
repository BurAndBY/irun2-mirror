from __future__ import unicode_literals

from django import template
from django.utils.encoding import smart_text
from django.utils.formats import number_format
from django.utils.translation import ugettext as _

from common.constants import NO, STDIN, STDOUT

from problems.utils import ProblemInfoManager

register = template.Library()


@register.inclusion_tag('problems/irunner_problems_difficulty_tag.html')
def irunner_problems_difficulty(difficulty, used=False):
    return {'difficulty': difficulty, 'used': used}


@register.inclusion_tag('problems/irunner_problems_statement_tag.html')
def irunner_problems_statement(statement, letter=None):
    return {'statement': statement, 'letter': letter}


@register.inclusion_tag('problems/irunner_problems_tutorial_tag.html')
def irunner_problems_tutorial(tutorial):
    return {'tutorial': tutorial}


@register.inclusion_tag('problems/irunner_problems_list_tag.html')
def irunner_problems_list(problems, pagination_context=None, list_is_complete=False, show_checkbox=False, query_string=''):
    manager = ProblemInfoManager(problems)
    return {
        'problems': problems,
        'infomanager': manager,
        'list_is_complete': list_is_complete,
        'pagination_context': pagination_context,
        'show_checkbox': show_checkbox,
        'query_string': query_string,
    }


@register.inclusion_tag('problems/irunner_problems_io_tag.html')
def irunner_problems_inputfile(filename):
    if filename:
        return {'filename': filename, 'emph': False}
    else:
        return {'filename': STDIN, 'emph': True}


@register.inclusion_tag('problems/irunner_problems_io_tag.html')
def irunner_problems_outputfile(filename):
    if filename:
        return {'filename': filename, 'emph': False}
    else:
        return {'filename': STDOUT, 'emph': True}


@register.inclusion_tag('problems/irunner_problems_tex_tag.html')
def irunner_problems_tex(form, render_url):
    return {'form': form, 'render_url': render_url}


@register.inclusion_tag('problems/irunner_problems_testparams_tag.html')
def irunner_problems_testparams(form):
    return {'form': form}


class Bounds(object):
    def __init__(self, default_value=0):
        self.min_value = None
        self.max_value = None
        self.default_value = None
        self.has_no = False

        if default_value:
            self.default_value = default_value

    def add(self, value):
        if value:
            self.min_value = value if self.min_value is None else min(value, self.min_value)
            self.max_value = value if self.max_value is None else max(value, self.max_value)
        else:
            self.has_no = True

    def has_values(self):
        return (self.min_value is not None and self.max_value is not None) or (self.has_no)

    def is_defined(self):
        return (self.default_value is not None) or (self.has_values())

    def as_string(self, formatter):
        tokens = []
        if self.has_values():
            if self.has_no:
                tokens.append(_('no'))
            if self.min_value is not None and self.max_value is not None:
                if self.min_value == self.max_value:
                    tokens.append(formatter(self.min_value))
                else:
                    tokens.append(_('from %(from)s to %(to)s') % {
                        'from': formatter(self.min_value), 'to': formatter(self.max_value)
                        })
        elif self.default_value is not None:
            tokens.append(formatter(self.default_value))
        return ', '.join(tokens)

from collections import namedtuple

LimitStrings = namedtuple('LimitStrings', 'time_limit memory_limit')


def time_formatter(value):
    if not value:
        return NO
    if value % 1000 == 0:
        # integer number of seconds
        seconds = smart_text(value // 1000)
    else:
        # use localized fraction representation
        seconds = number_format(value / 1000)
    return _('%(seconds)s s') % {'seconds': seconds}


def memory_formatter(value):
    if not value:
        return NO
    if value % (1024 * 1024) == 0:
        megabytes = smart_text(value // (1024 * 1024))
    else:
        megabytes = number_format(float(value) / (1024 * 1024))
    return _('%(megabytes)s MB') % {'megabytes': megabytes}


def represent_limits(problem):
    time_limit = Bounds(problem.get_default_time_limit())
    memory_limit = Bounds(problem.get_default_memory_limit())
    for tl, ml in problem.testcase_set.values_list('time_limit', 'memory_limit'):
        time_limit.add(tl)
        memory_limit.add(ml)

    return LimitStrings(time_limit.as_string(time_formatter), memory_limit.as_string(memory_formatter))


@register.inclusion_tag('problems/irunner_problems_heading_tag.html')
def irunner_problems_heading(problem, letter=None, lang_selector=None):
    ls = represent_limits(problem)

    if lang_selector is None:
        name = problem.numbered_full_name()
    else:
        name = problem.numbered_full_name_for_lang(lang_selector.get_current_lang())

    return {
        'problem': problem,
        'problem_name': name,
        'letter': letter,
        'time_limit': ls.time_limit,
        'memory_limit': ls.memory_limit,
        'lang_selector': lang_selector,
    }


@register.simple_tag
def irunner_problems_timelimit(value):
    return time_formatter(value)


@register.simple_tag
def irunner_problems_memorylimit(value):
    return memory_formatter(value)


@register.simple_tag
def irunner_problems_getinfo(problem_id, manager):
    return manager.get(problem_id)

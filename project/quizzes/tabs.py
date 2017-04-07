from django.utils.translation import ugettext_lazy as _

from collections import namedtuple

Tab = namedtuple('Tab', 'name icon url_pattern')


class Tabs(object):
    GROUPS = Tab(_('Question groups'), 'question-sign', 'quizzes:groups:list')
    TEMPLATES = Tab(_('Quiz templates'), 'list', 'quizzes:templates:list')

    ALL = [
        GROUPS,
        TEMPLATES
    ]

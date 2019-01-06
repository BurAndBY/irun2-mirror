from django.utils.translation import ugettext_lazy as _

from collections import namedtuple

Tab = namedtuple('Tab', 'name icon url_pattern')


class Tabs(object):
    CATEGORIES = Tab(_('Question categories'), 'question-sign', 'quizzes:categories:list')
    TEMPLATES = Tab(_('Quiz templates'), 'list', 'quizzes:templates:list')

    ALL = [
        CATEGORIES,
        TEMPLATES
    ]

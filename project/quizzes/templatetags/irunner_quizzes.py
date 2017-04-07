from django import template
from django.utils.html import escape

from common.katex import tex2html

from quizzes.models import Question

register = template.Library()


@register.inclusion_tag('quizzes/irunner_quizzes_showquestion.html')
def irunner_quizzes_showquestion(question):
    preparer = escape if (question.kind == Question.TEXT_ANSWER) else tex2html
    return {
        'text': tex2html(question.text),
        'choices': [
            (preparer(ch.text), ch.is_right) for ch in question.choice_set.order_by('id')
        ],
    }

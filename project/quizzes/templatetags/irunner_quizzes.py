from django import template
from django.utils.html import escape

from collections import namedtuple

from common.katex import tex2html

from quizzes.models import Question

register = template.Library()

SessionAnswerInfo = namedtuple('SessionAnswerInfo', 'text is_right is_wrong is_notchosen')


@register.inclusion_tag('quizzes/irunner_quizzes_showquestion.html')
def irunner_quizzes_showquestion(question):
    preparer = escape if (question.kind == Question.TEXT_ANSWER) else tex2html
    return {
        'text': tex2html(question.text),
        'choices': [
            (preparer(ch.text), ch.is_right) for ch in question.choice_set.order_by('id')
        ],
    }


@register.inclusion_tag('quizzes/irunner_quizzes_showanswer.html')
def irunner_quizzes_showanswer(session_question, counter):
    is_text = (session_question.question.kind == Question.TEXT_ANSWER)
    preparer = escape if is_text else tex2html
    answers = []
    for answer in session_question.sessionquestionanswer_set.order_by('id').select_related('choice'):
        if is_text:
            if answer.choice.text == answer.user_answer:
                answers.append(SessionAnswerInfo(preparer(answer.user_answer), True, False, False))
            else:
                answers.append(SessionAnswerInfo(preparer(answer.choice.text), False, False, True))
                answers.append(SessionAnswerInfo(preparer('' if answer.user_answer is None else answer.user_answer),
                                                 False, True, False))
        else:
            is_right = answer.is_chosen and answer.choice.is_right
            is_wrong = answer.is_chosen and not answer.choice.is_right
            is_notchosen = not answer.is_chosen and answer.choice.is_right
            answers.append(SessionAnswerInfo(preparer(answer.choice.text), is_right, is_wrong, is_notchosen))
    eps = 0.000001
    return {
        'text': tex2html(session_question.question.text),
        'points': round(session_question.points + eps, 1),
        'result_points': round(session_question.result_points + eps, 1),
        'counter': counter,
        'answers': answers,
    }

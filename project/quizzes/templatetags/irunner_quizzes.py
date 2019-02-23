from django import template
from django.utils.html import escape, format_html

from collections import namedtuple

from common.katex import tex2html

from quizzes.constants import NO_CATEGORY_SLUG
from quizzes.models import Question

register = template.Library()

SessionAnswerInfo = namedtuple('SessionAnswerInfo', 'text is_right is_wrong is_notchosen')


@register.inclusion_tag('quizzes/irunner_quizzes_showquestion.html')
def irunner_quizzes_showquestion(question, category_slug, can_edit=False):
    preparer = escape if (question.kind == Question.TEXT_ANSWER) else tex2html
    return {
        'id': question.id,
        'category_slug': category_slug,
        'group_id': question.group_id,
        'text': tex2html(question.text),
        'choices': [
            (preparer(ch.text), ch.is_right) for ch in question.choice_set.order_by('id')
        ],
        'can_edit': can_edit,
    }


@register.inclusion_tag('quizzes/irunner_quizzes_showanswer.html')
def irunner_quizzes_showanswer(session_question, counter, save_mark_url=None):
    is_text = (session_question.question.kind in [Question.TEXT_ANSWER, Question.OPEN_ANSWER])
    preparer = escape if is_text else tex2html
    answers = []
    for answer in session_question.sessionquestionanswer_set.order_by('id').select_related('choice'):
        if is_text and session_question.question.kind == Question.TEXT_ANSWER:
            if answer.choice.text == answer.user_answer:
                answers.append(SessionAnswerInfo(preparer(answer.user_answer), True, False, False))
            else:
                answers.append(SessionAnswerInfo(preparer(answer.choice.text), False, False, True))
                answers.append(SessionAnswerInfo(preparer('' if answer.user_answer is None else answer.user_answer),
                                                 False, True, False))
        elif is_text and session_question.question.kind == Question.OPEN_ANSWER:
            answers.append(SessionAnswerInfo(preparer('' if answer.user_answer is None else answer.user_answer),
                                                 False, False, False))
        else:
            is_right = answer.is_chosen and answer.choice.is_right
            is_wrong = answer.is_chosen and not answer.choice.is_right
            is_notchosen = not answer.is_chosen and answer.choice.is_right
            answers.append(SessionAnswerInfo(preparer(answer.choice.text), is_right, is_wrong, is_notchosen))
    eps = 0.000001
    return {
        'question_id': session_question.id,
        'text': tex2html(session_question.question.text),
        'points': round(session_question.points + eps, 1),
        'result_points': round(session_question.result_points + eps, 1),
        'counter': counter,
        'answers': answers,
        'is_editable': save_mark_url is not None and session_question.question.kind == Question.OPEN_ANSWER,
        'save_mark_url': save_mark_url,
    }


@register.simple_tag
def irunner_quizzes_mark(result, is_finished=True, pending_manual_check=False):
    value = int(result) if (result is not None and is_finished) else '?'
    if pending_manual_check:
        return format_html('<div class="ir-quiz-pending-mark">{}</div>', value)
    return format_html('<div class="ir-quiz-mark">{}</div>', value)


@register.inclusion_tag('quizzes/irunner_quizzes_breadcrumbs.html', takes_context=True)
def irunner_quizzes_breadcrumbs(context, question=False):
    if 'category' in context:
        category = context['category']  # may be None
        return {
            'has_category': True,
            'category': category,
            'category_slug': category.slug if category is not None else NO_CATEGORY_SLUG,
            'group': context.get('group'),
            'question': question,
        }
    return {}

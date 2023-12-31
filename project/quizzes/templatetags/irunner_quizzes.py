from django import template
from django.utils.html import escape, format_html, mark_safe

from collections import namedtuple

from common.pylightex import tex2html

from quizzes.constants import NO_CATEGORY_SLUG
from quizzes.models import Question

register = template.Library()

SessionAnswerInfo = namedtuple('SessionAnswerInfo', 'id text is_right is_wrong is_notchosen view_raw')


def make_session_answer_info(answer_id, text, is_right=False, is_wrong=False, is_notchosen=False, view_raw=False):
    return SessionAnswerInfo(answer_id, text, is_right, is_wrong, is_notchosen, view_raw)


def escape_preparer(tex, inline):
    return escape(tex)


def tex2html_preparer(tex, inline, throw=False):
    return mark_safe(tex2html(tex, inline=inline, throw=throw))


@register.inclusion_tag('quizzes/irunner_quizzes_showquestion.html')
def irunner_quizzes_showquestion(question, category_slug, can_edit=False):
    preparer = escape_preparer if (question.kind == Question.TEXT_ANSWER) else tex2html_preparer
    return {
        'id': question.id,
        'category_slug': category_slug,
        'group_id': question.group_id,
        'text': tex2html_preparer(question.text, inline=False),
        'choices': [
            (preparer(ch.text, inline=True), ch.is_right) for ch in question.choice_set.order_by('id')
        ],
        'can_edit': can_edit,
    }


@register.inclusion_tag('quizzes/irunner_quizzes_showanswer.html')
def irunner_quizzes_showanswer(session_question, counter, save_mark_url=None, sessionquestionanswer_cache=None):
    is_text = (session_question.question.kind == Question.TEXT_ANSWER)
    preparer = escape_preparer if is_text else tex2html_preparer
    answers = []
    if sessionquestionanswer_cache is not None:
        qs = sessionquestionanswer_cache.get(session_question.id, [])
    else:
        qs = session_question.sessionquestionanswer_set.order_by('id').select_related('choice')
    for answer in qs:
        if is_text:
            if answer.choice.text == answer.user_answer:
                answers.append(make_session_answer_info(answer.id, preparer(answer.user_answer, inline=True), is_right=True))
            else:
                answers.append(make_session_answer_info(answer.id, preparer(answer.choice.text, inline=True), is_notchosen=True))
                answers.append(make_session_answer_info(answer.id, preparer('' if answer.user_answer is None else answer.user_answer, inline=True), is_wrong=True))
        elif session_question.question.kind == Question.OPEN_ANSWER:
            src = '' if answer.user_answer is None else answer.user_answer
            try:
                answers.append(make_session_answer_info(answer.id, tex2html_preparer(src, inline=False, throw=True), view_raw=len(src) > 0))
            except:
                answers.append(make_session_answer_info(answer.id, escape_preparer(src, inline=True)))
        else:
            answers.append(make_session_answer_info(
                answer.id,
                preparer(answer.choice.text, inline=True),
                is_right=answer.is_chosen and answer.choice.is_right,
                is_wrong=answer.is_chosen and not answer.choice.is_right,
                is_notchosen=not answer.is_chosen and answer.choice.is_right,
            ))
    eps = 0.000001
    return {
        'question_id': session_question.id,
        'text': tex2html_preparer(session_question.question.text, inline=False),
        'points': round(session_question.points + eps, 1),
        'result_points': round(session_question.result_points + eps, 1),
        'counter': counter,
        'answers': answers,
        'is_editable': save_mark_url is not None and session_question.question.kind == Question.OPEN_ANSWER,
        'save_mark_url': save_mark_url,
    }


@register.simple_tag
def irunner_quizzes_mark(result, is_finished=True, pending_manual_check=False, finish_time=None, deadline=None):
    after_deadline = finish_time is not None and deadline is not None and finish_time > deadline
    value = int(result) if (result is not None and is_finished) else '?'
    if pending_manual_check:
        if after_deadline:
            return format_html('<div class="ir-quiz-pending-after-deadline-mark">{}</div>', value)
        return format_html('<div class="ir-quiz-pending-mark">{}</div>', value)
    return format_html('<div class="ir-quiz-mark">{}</div>', value)


@register.inclusion_tag('quizzes/irunner_quizzes_breadcrumbs.html', takes_context=True)
def irunner_quizzes_breadcrumbs(context, section=None):
    if 'category' in context:
        category = context['category']  # may be None
        return {
            'has_category': True,
            'category': category,
            'category_slug': category.slug if category is not None else NO_CATEGORY_SLUG,
            'group': context.get('group'),
            'section': section,
        }
    return {}


@register.inclusion_tag('quizzes/irunner_quizzes_showcomment.html')
def irunner_quizzes_showcomment(comment, user_cache):
    try:
        text = tex2html_preparer(comment.text, inline=False, throw=True)
    except:
        text = escape_preparer(comment.text, inline=True)
    return {
        'text': text,
        'comment': comment,
        'user_cache': user_cache,
    }

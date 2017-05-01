from __future__ import unicode_literals

from django.utils import timezone
from django.db import transaction
from django.utils.translation import ugettext as _
import random

from common.katex import tex2html
from quizzes.answer_checker import CHECKERS
from quizzes.models import QuizSession, GroupQuizRelation, SessionQuestion, SessionQuestionAnswer, Question


@transaction.atomic
def create_session(instance, user):
    session = QuizSession.objects.create(quiz_instance=instance, user=user, start_time=timezone.now())
    groups = list(instance.quiz_template.question_groups.all())
    if instance.quiz_template.shuffle_questions:
        random.shuffle(groups)
    questions = []
    for idx, group in enumerate(groups):
        qs = group.question_set.order_by('pk')
        q = qs[random.randint(0, qs.count() - 1)]
        rel = GroupQuizRelation.objects.get(template=instance.quiz_template, group=group)
        questions.append(SessionQuestion(quiz_session=session, order=idx, points=rel.points, question=q))
    SessionQuestion.objects.bulk_create(questions)
    questions = SessionQuestion.objects.filter(quiz_session=session)\
        .select_related('question').prefetch_related('question__choice_set')
    answers = []
    for q in questions:
        for c in q.question.choice_set.all():
            answers.append(SessionQuestionAnswer(session_question=q, choice=c))
    SessionQuestionAnswer.objects.bulk_create(answers)
    return session


def get_quiz_data(session):
    quiz_data = {
        'id': session.id,
        'name': session.quiz_instance.quiz_template.name,
        'timeLeft': int((session.start_time + session.quiz_instance.time_limit - timezone.now()).total_seconds())
    }
    questions = []
    for q in session.sessionquestion_set.order_by('order').\
            select_related('question').prefetch_related('sessionquestionanswer_set', 'sessionquestionanswer_set__choice'):
        choices = []
        for a in q.sessionquestionanswer_set.all():
            if q.question.kind == Question.TEXT_ANSWER:
                choices.append({'id': a.id, 'chosen': a.is_chosen, 'userAnswer': a.user_answer})
            else:
                choices.append({'id': a.id, 'chosen': a.is_chosen, 'text': tex2html(a.choice.text)})
        questions.append({'id': q.id, 'text': tex2html(q.question.text), 'type': q.question.kind, 'choices': choices})
    quiz_data['questions'] = questions
    return quiz_data


@transaction.atomic
def check_quiz_answers(session):
    res = 0.
    max_res = 0.
    for question in session.sessionquestion_set.select_related('question').all():
        max_res += question.points
        checker = CHECKERS[question.question.kind]
        q_result = checker.get_result_points(question)
        res += q_result
        question.result_points = q_result
        question.save()
    session.result = calc_ten_point_grade(res, max_res)
    session.is_finished = True
    session.finish_time = min(session.start_time + session.quiz_instance.time_limit, timezone.now())
    session.save()


def calc_ten_point_grade(res, max_res):
    eps = 0.000001
    return 0. if max_res == 0 else round(res / max_res * 10. + eps)


def finish_overdue_sessions(sessions):
    for session in sessions:
        finish_overdue_session(session)


def finish_overdue_session(session):
    if not session.is_finished \
            and timezone.now() - session.start_time > session.quiz_instance.time_limit:
        check_quiz_answers(session)


def get_quiz_page_language_tags():
    return {
        'question': _('Question'),
        'finish': _('Finish'),
        'ok': _('OK'),
        'no': _('No'),
        'error': _('Error'),
        'cancel': _('Cancel'),
        'next': _('Next'),
        'previous': _('Previous'),
        'networkError': _('Network error'),
        'noTimeLeft': _('No time left')
    }

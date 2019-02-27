from __future__ import unicode_literals

from django.utils import timezone
from django.db import transaction
from django.utils.translation import ugettext as _
import random
from collections import Counter

from common.pylightex import tex2html
from quizzes.answer_checker import CHECKERS
from quizzes.models import QuizSession, SessionQuestion, SessionQuestionAnswer, Question, QuestionGroup, Choice


QUESTION_KINDS = {
    'single': Question.SINGLE_ANSWER,
    'multiple': Question.MULTIPLE_ANSWERS,
    'text': Question.TEXT_ANSWER,
    'open': Question.OPEN_ANSWER,
}

QUESTION_KINDS_BY_ID = {
    Question.SINGLE_ANSWER: 'single',
    Question.MULTIPLE_ANSWERS: 'multiple',
    Question.TEXT_ANSWER: 'text',
    Question.OPEN_ANSWER: 'open',
}


@transaction.atomic
def create_session(instance, user):
    session = QuizSession.objects.create(quiz_instance=instance, user=user, start_time=timezone.now(),
                                         score_policy=instance.quiz_template.score_policy)
    relations = list(instance.quiz_template.groupquizrelation_set.all().select_related('group'))

    count_by_group = Counter()
    for rel in relations:
        count_by_group[rel.group_id] += 1

    questions_by_group = {}
    for group_id, required_count in count_by_group.items():
        qs = Question.objects.filter(group_id=group_id, is_deleted=False).order_by('pk')
        available_count = qs.count()
        questions_by_group[group_id] = [qs[i] for i in random.sample(range(available_count), min(required_count, available_count))]

    if instance.quiz_template.shuffle_questions:
        random.shuffle(relations)
    questions = []
    for idx, rel in enumerate(relations):
        qs = questions_by_group[rel.group_id]
        if qs:
            q = qs.pop()
            questions.append(SessionQuestion(quiz_session=session, order=idx, points=rel.points, question=q))

    SessionQuestion.objects.bulk_create(questions)
    questions = SessionQuestion.objects.filter(quiz_session=session)\
        .select_related('question').prefetch_related('question__choice_set')
    answers = []
    requires_manual_check = False
    for q in questions:
        for c in q.question.choice_set.all():
            answers.append(SessionQuestionAnswer(session_question=q, choice=c))
        if q.question.kind == Question.OPEN_ANSWER:
            answers.append(SessionQuestionAnswer(session_question=q))
            requires_manual_check = True
    session.pending_manual_check = requires_manual_check
    session.save()
    SessionQuestionAnswer.objects.bulk_create(answers)
    return session


def get_quiz_data(session):
    quiz_data = {
        'id': session.id,
        'name': session.quiz_instance.quiz_template.name,
        'timeLeft': (session.start_time + session.quiz_instance.time_limit - timezone.now()).total_seconds()
    }
    questions = []
    for q in session.sessionquestion_set.order_by('order').\
            select_related('question').prefetch_related('sessionquestionanswer_set', 'sessionquestionanswer_set__choice'):
        choices = []
        for a in q.sessionquestionanswer_set.all():
            if q.question.kind in [Question.TEXT_ANSWER, Question.OPEN_ANSWER]:
                choices.append({'id': a.id, 'chosen': a.is_chosen, 'userAnswer': a.user_answer})
            else:
                choices.append({'id': a.id, 'chosen': a.is_chosen, 'text': tex2html(a.choice.text, inline=True)})
        questions.append({'id': q.id, 'text': tex2html(q.question.text, inline=False), 'type': q.question.kind, 'choices': choices})
    quiz_data['questions'] = questions
    return quiz_data


@transaction.atomic
def check_quiz_answers(session):
    res = 0.
    max_res = 0.
    for question in session.sessionquestion_set.select_related('question').all():
        max_res += question.points
        checker = CHECKERS[question.question.kind]
        q_result = checker.get_result_points(question, session.score_policy)
        res += q_result
        question.result_points = q_result
        question.save()
    session.result = calc_ten_point_grade(res, max_res)
    if not session.is_finished:
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


def is_question_valid(question):
    num_choices = len(question.choices)
    correct_choices = sum(c.is_right for c in question.choices)
    if question.type == QUESTION_KINDS_BY_ID[Question.SINGLE_ANSWER]:
        return num_choices >= 0 and correct_choices == 1
    elif question.type == QUESTION_KINDS_BY_ID[Question.MULTIPLE_ANSWERS]:
        return num_choices >= 0 and correct_choices >= 1
    elif question.type == QUESTION_KINDS_BY_ID[Question.TEXT_ANSWER]:
        return num_choices == 1 and correct_choices == 1
    elif question.type == QUESTION_KINDS_BY_ID[Question.OPEN_ANSWER]:
        return num_choices == 0 and correct_choices == 0
    else:
        return False


def is_relation_valid(relation):
    return relation.points >= 0


@transaction.atomic
def add_questions_to_question_group(group, questions_data):

    for question_data in questions_data:
        q = Question.objects.create(group=group, text=question_data.text, kind=QUESTION_KINDS[question_data.type])
        choices = []
        for c in question_data.choices:
            choices.append(Choice(question=q, text=c.text, is_right=c.is_right))
        Choice.objects.bulk_create(choices)


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
        'noTimeLeft': _('No time left'),
        'quizIsOver': _('Quiz is over'),
    }


def get_empty_question_data(kind):
    return {
        'id': None,
        'text': _('Type the question text here...'),
        'type': QUESTION_KINDS_BY_ID[kind],
        'choices': [{
            'text': _('Type the choice text here...'),
            'is_right': True
        }] if kind != Question.OPEN_ANSWER else [],
    }


def get_question_editor_language_tags():
    return {
        'questionText': _('Question text'),
        'questionType': _('Question type'),
        'isRight': _('Is correct'),
        'singleAnswer': _('Single correct answer'),
        'multipleAnswers': _('Multiple correct answers'),
        'textAnswer': _('Text answer'),
        'openAnswer': _('Open answer'),
        'addChoice': _('Add choice'),
        'defaultQuestionText': _('Type the question text here...'),
        'defaultChoiceText': _('Type the choice text here...'),
        'refreshPreview': _('Refresh preview'),
    }

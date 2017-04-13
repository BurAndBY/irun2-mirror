import json

from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _
from rest_framework.views import APIView

from courses.views import BaseCourseView
from quizzes.models import QuizInstance, QuizSession, SessionQuestionAnswer, Question
from collections import namedtuple

from rest_framework.response import Response

from quizzes.quizstructs import SaveAnswerMessage
from quizzes.serializers import QuizAnswersDataSerializer, SaveAnswerMessageSerializer
from quizzes.utils import create_session, finish_overdue_session, get_quiz_data, get_quiz_page_language_tags, \
    finish_overdue_sessions, check_quiz_answers

QuizInfo = namedtuple('QuizInfo', 'instance can_start attempts_left question_count sessions')


class QuizMixin(object):
    tab = 'quizzes'

    def is_allowed(self, permissions):
        return permissions.info


class CourseQuizzesView(QuizMixin, BaseCourseView):
    template_name = 'courses/quizzes.html'

    def make_quiz_info(self, instance):
        my_sessions = QuizSession.objects.filter(quiz_instance=instance, user=self.request.user)
        finish_overdue_sessions(my_sessions)
        attempts_left = None if instance.attempts is None else max(0, instance.attempts - len(my_sessions))
        can_start = instance.is_available and (attempts_left is None or attempts_left > 0)
        question_count = instance.quiz_template.question_groups.count()  # TODO implement normal counting
        return QuizInfo(instance, can_start, attempts_left, question_count, my_sessions)

    def get(self, request, course):
        context = self.get_context_data()
        instances = QuizInstance.objects.filter(course=course).select_related('quiz_template').order_by('id')
        context['quizzes'] = [self.make_quiz_info(instance) for instance in instances]
        return render(request, self.template_name, context)


class CourseQuizzesStartView(QuizMixin, BaseCourseView):

    def post(self, request, course, instance_id):
        instance = QuizInstance.objects.filter(pk=instance_id, course=course).first()
        if instance is None:
            return redirect('courses:quizzes:list', course.id)
        attempts = QuizSession.objects.filter(quiz_instance=instance, user=self.request.user).count()
        attempts_left = None if instance.attempts is None else max(0, instance.attempts - attempts)
        can_start = instance.is_available and (attempts_left is None or attempts_left > 0)
        if not can_start:
            return redirect('courses:quizzes:list', course.id)
        session = create_session(instance, request.user)
        return redirect('courses:quizzes:session', course.id, session.id)


class CourseQuizzesSessionView(QuizMixin, BaseCourseView):
    template_name = 'courses/quiz.html'

    def get_urls(self, course_id, session_id):
        return {
            'save_answer': '/courses/{}/quizzes/sessions/{}/save-answer/'.format(course_id, session_id),
            'home': '/courses/{}/quizzes/'.format(course_id),
        }

    def get(self, request, course, session_id):
        session = QuizSession.objects.filter(pk=session_id, user=request.user).first()
        if session is None:
            return redirect('courses:quizzes:list', course.id)
        finish_overdue_session(session)
        if session.is_finished:
            return redirect('courses:quizzes:answers', course.id, session.id)
        context = self.get_context_data()
        context['quizData'] = json.dumps(get_quiz_data(session))
        context['tags'] = json.dumps(get_quiz_page_language_tags())
        context['urls'] = json.dumps(self.get_urls(course.id, session_id))
        context['session'] = session
        return render(request, self.template_name, context)


class CourseQuizzesFinishView(QuizMixin, BaseCourseView):
    template_name = 'courses/quiz.html'

    def post(self, request, course, session_id):
        session = QuizSession.objects.filter(pk=session_id, user=request.user).first()
        if session is None:
            return redirect('courses:quizzes:list', course.id)
        if not session.is_finished:
            check_quiz_answers(session)
        return redirect('courses:quizzes:answers', course.id, session.id)


class SaveAnswerAPIView(APIView):

    def respond_with_message(self, message, status):
        return Response(SaveAnswerMessageSerializer(SaveAnswerMessage(message)).data, status=status)

    def post(self, request, course_id, session_id):
        if not request.user.is_authenticated:
            return self.respond_with_message(_('Permission denied'), 403)
        session = QuizSession.objects.filter(pk=session_id, user=request.user).first()
        if session is None:
            return self.respond_with_message(_('Quiz does not exist'), 404)
        finish_overdue_session(session)
        if session.is_finished:
            return self.respond_with_message(
                _('Quiz is finished or no time is left. Do you want to go to results page?'), 410)
        serializer = QuizAnswersDataSerializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            return self.respond_with_message(_('Request is not valid'), 400)
        answers_data = serializer.save()
        for answer in answers_data.answers:
            try:
                a = SessionQuestionAnswer.objects.get(pk=answer.id, session_question__quiz_session=session)
                if a.session_question.question.kind == Question.TEXT_ANSWER:
                    a.user_answer = answer.user_answer
                else:
                    a.is_chosen = answer.chosen
                a.save()
            except SessionQuestionAnswer.DoesNotExist:
                continue
        return Response({}, status=200)

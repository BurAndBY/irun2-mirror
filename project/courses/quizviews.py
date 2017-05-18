import json

from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from rest_framework import status
from rest_framework.views import APIView

from common.networkutils import never_ever_cache
from courses.views import BaseCourseView, UserCacheMixinMixin
from quizzes.models import QuizInstance, QuizSession, SessionQuestionAnswer, Question
from collections import namedtuple

from rest_framework.response import Response

from quizzes.quizstructs import SaveAnswerMessage
from quizzes.serializers import QuizAnswersDataSerializer, SaveAnswerMessageSerializer
from quizzes.utils import create_session, finish_overdue_session, get_quiz_data, get_quiz_page_language_tags, \
    finish_overdue_sessions, check_quiz_answers

QuizInfo = namedtuple('QuizInfo', 'instance can_start attempts_left question_count sessions')
SessionInfo = namedtuple('SessionInfo', 'session is_own result')


class QuizMixin(object):
    tab = 'quizzes'


class CourseQuizzesView(QuizMixin, BaseCourseView):
    template_name = 'courses/quizzes.html'

    def is_allowed(self, permissions):
        return permissions.quizzes or permissions.quizzes_admin

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

    def is_allowed(self, permissions):
        return permissions.quizzes or permissions.quizzes_admin

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

    def is_allowed(self, permissions):
        return permissions.quizzes or permissions.quizzes_admin

    def get_urls(self, session_id):
        return {
            'save_answer': reverse('courses:quizzes:save_answer',
                                   kwargs={'course_id': self.course.id, 'session_id': session_id}),
            'home': reverse('courses:quizzes:list', kwargs={'course_id': self.course.id}),
        }

    @method_decorator(never_ever_cache)
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
        context['urls'] = json.dumps(self.get_urls(session_id))
        context['session'] = session
        return render(request, self.template_name, context)


class CourseQuizzesFinishView(QuizMixin, BaseCourseView):
    template_name = 'courses/quiz.html'

    def is_allowed(self, permissions):
        return permissions.quizzes or permissions.quizzes_admin

    def post(self, request, course, session_id):
        session = QuizSession.objects.filter(pk=session_id, user=request.user).first()
        if session is None:
            return redirect('courses:quizzes:list', course.id)
        if not session.is_finished:
            check_quiz_answers(session)
        return redirect('courses:quizzes:answers', course.id, session.id)


class SaveAnswerAPIView(APIView):

    def respond_with_message(self, message, status_code):
        return Response(SaveAnswerMessageSerializer(SaveAnswerMessage(message)).data, status=status_code)

    def post(self, request, course_id, session_id):
        if not request.user.is_authenticated:
            return self.respond_with_message(_('Permission denied'), status.HTTP_403_FORBIDDEN)
        session = QuizSession.objects.filter(pk=session_id, user=request.user).first()
        if session is None:
            return self.respond_with_message(_('Quiz does not exist'), status.HTTP_404_NOT_FOUND)
        finish_overdue_session(session)
        if session.is_finished:
            return self.respond_with_message(
                _('Quiz is finished or no time is left. Do you want to go to home page?'), status.HTTP_410_GONE)
        serializer = QuizAnswersDataSerializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            return self.respond_with_message(_('Request is not valid'), status.HTTP_400_BAD_REQUEST)
        answers_data = serializer.save()
        with transaction.atomic():
            for answer in answers_data.answers:
                kwargs = {}
                if answer.chosen is not None:
                    kwargs['is_chosen'] = answer.chosen
                if answer.user_answer is not None:
                    kwargs['user_answer'] = answer.user_answer

                SessionQuestionAnswer.objects.filter(pk=answer.id, session_question__quiz_session=session).update(
                    **kwargs)
        return Response({}, status=status.HTTP_200_OK)


class CourseQuizzesAnswersView(QuizMixin, UserCacheMixinMixin, BaseCourseView):
    template_name = 'courses/quizzes_answers.html'

    def is_allowed(self, permissions):
        return permissions.quizzes or permissions.quizzes_admin

    def get_session_info(self, session):
        answers = session.sessionquestion_set.order_by('order').select_related('question')
        result_points = 0
        points = 0
        for answer in answers:
            points += answer.points
            result_points += answer.result_points
        eps = 0.000001
        info = {
            'name': session.quiz_instance.quiz_template.name,
            'result': session.result,
            'start_time': session.start_time,
            'finish_time': session.finish_time,
            'answers': answers,
            'user_id': session.user_id,
            'points': round(points + eps, 1),
            'result_points': round(result_points + eps, 1),
        }
        return info

    def _fetch_session(self, session_id):
        session = QuizSession.objects.\
            filter(pk=session_id, quiz_instance__course=self.course).\
            select_related('quiz_instance').first()

        if session is None:
            return None

        if session.user_id != self.request.user.id and not self.permissions.quizzes_admin:
            return None

        if not session.quiz_instance.show_answers and not self.permissions.quizzes_admin:
            return None

        finish_overdue_session(session)
        if not session.is_finished:
            return None

        return session

    def get(self, request, course, session_id):
        session = self._fetch_session(session_id)
        if session is None:
            return redirect('courses:quizzes:list', course.id)
        context = self.get_context_data()
        context['quiz'] = self.get_session_info(session)
        context['session'] = session
        context['can_delete'] = self.permissions.quizzes_admin
        return render(request, self.template_name, context)


class CourseQuizzesRatingView(QuizMixin, UserCacheMixinMixin, BaseCourseView):
    template_name = 'courses/quizzes_rating.html'

    def is_allowed(self, permissions):
        return permissions.quizzes or permissions.quizzes_admin

    def make_session_info(self, session, user):
        is_own = session.user_id == user.id
        result = session.result
        return SessionInfo(session, is_own, result)

    def get(self, request, course, instance_id):
        context = self.get_context_data()
        # TODO filter teachers and admins
        instance = QuizInstance.objects.filter(pk=instance_id, course=course).select_related('quiz_template').first()
        if instance is None or instance.attempts != 1:
            return redirect('courses:quizzes:list', course.id)
        sessions = QuizSession.objects.filter(quiz_instance=instance, is_finished=True).\
            select_related('user').order_by('-result', 'start_time')
        context['sessions'] = [self.make_session_info(session, request.user) for session in sessions]
        context['instance'] = instance
        context['can_manage'] = self.permissions.quizzes_admin
        return render(request, self.template_name, context)


class CourseQuizzesDeleteSessionView(QuizMixin, BaseCourseView):

    def is_allowed(self, permissions):
        return permissions.quizzes_admin

    def post(self, request, course, session_id):
        session = QuizSession.objects.filter(pk=session_id, quiz_instance__course=course).first()
        if session is not None:
            instance_id = session.quiz_instance_id
            session.delete()
            return redirect('courses:quizzes:rating', course.id, instance_id)
        return redirect('courses:quizzes:list', course.id)


QuizInstanceUserResult = namedtuple('QuizInstanceUserResult', 'user_id sessions')
QuizInstanceResults = namedtuple('CourseResults', 'user_results stats average_mark')
QuizStudentCount = namedtuple('QuizStudentCount', 'total passing passed')


def make_quiz_instance_results(course, user_cache, instance):
    user_results = []
    user_id_to_sessions = {}
    user_id_to_state = {}

    marks = []

    for user in user_cache.list_students():
        sessions = user_id_to_sessions.setdefault(user.id, [])
        user_results.append(QuizInstanceUserResult(user.id, sessions))

    for session in QuizSession.objects.filter(quiz_instance=instance).order_by('start_time'):
        finish_overdue_session(session)
        sessions = user_id_to_sessions.get(session.user_id)
        if sessions is not None:
            sessions.append(session)
            user_id_to_state[session.user_id] = user_id_to_state.get(session.user_id, False) or session.is_finished
            if session.is_finished:
                marks.append(session.result)

    stats = QuizStudentCount(
        total=len(user_results),
        passing=user_id_to_state.values().count(False),
        passed=user_id_to_state.values().count(True),
    )

    average_mark = 1. * sum(marks) / len(marks) if marks else 0.

    return QuizInstanceResults(user_results, stats, average_mark)


class CourseQuizzesSheetView(QuizMixin, UserCacheMixinMixin, BaseCourseView):
    template_name = 'courses/quizzes_sheet.html'

    def is_allowed(self, permissions):
        return permissions.quizzes_admin

    def get(self, request, course, instance_id):
        instance = QuizInstance.objects.filter(pk=instance_id, course=course).select_related('quiz_template').first()
        if instance is None:
            return redirect('courses:quizzes:list', course.id)

        data = make_quiz_instance_results(course, self.get_user_cache(), instance)

        context = self.get_context_data(instance=instance, data=data)
        return render(request, self.template_name, context)


class CourseQuizzesTurnOnView(BaseCourseView):
    def is_allowed(self, permissions):
        return permissions.quizzes_admin

    def post(self, request, course, instance_id):
        QuizInstance.objects.filter(pk=instance_id, course=course).update(is_available=True)
        return redirect('courses:quizzes:list', course.id)


class CourseQuizzesTurnOffView(BaseCourseView):
    def is_allowed(self, permissions):
        return permissions.quizzes_admin

    def post(self, request, course, instance_id):
        QuizInstance.objects.filter(pk=instance_id, course=course).update(is_available=False)
        return redirect('courses:quizzes:list', course.id)

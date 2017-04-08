import json

from django.shortcuts import render, redirect

from courses.views import BaseCourseView
from quizzes.models import QuizInstance, QuizSession
from collections import namedtuple

from quizzes.utils import create_session, finish_overdue_session, get_quiz_data, get_quiz_page_language_tags, \
    finish_overdue_sessions

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
        return render(request, self.template_name, context)



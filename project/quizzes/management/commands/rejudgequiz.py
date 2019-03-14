from __future__ import print_function

from django.core.management.base import BaseCommand

from quizzes.models import QuizSession
from quizzes.utils import check_quiz_answers


class Command(BaseCommand):
    help = 'The tool fixes result points in quiz sessions that include questions from the given question group'

    def add_arguments(self, parser):
        parser.add_argument('questiongroupid')

    def handle(self, *args, **options):
        for session in QuizSession.objects.filter(sessionquestion__question__group=options['questiongroupid']).distinct():
            print('Session', session.id)
            check_quiz_answers(session)

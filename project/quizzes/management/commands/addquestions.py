from django.core.management.base import BaseCommand
from quizzes.models import QuestionGroup, Question, Choice
from django.db import transaction
import json


class Command(BaseCommand):
    help = 'Imports questions from file into database.'

    def add_arguments(self, parser):
        parser.add_argument('filename')

    def handle(self, *args, **options):
        filename = options['filename']
        f = open(filename, 'r')
        groups = json.load(f)
        f.close()
        for group in groups:
            add_group(group)


@transaction.atomic
def add_group(group):
    gs = QuestionGroup.objects.filter(name=group['name']).all()
    if len(gs) > 0:
        g = gs[0]
    else:
        g = QuestionGroup.objects.create(name=group['name'])
    for q in group['questions']:
        add_question(g, q)


def add_question(group, question):
    kinds = {
        'single': Question.SINGLE_ANSWER,
        'multiple': Question.MULTIPLE_ANSWERS,
        'text': Question.TEXT_ANSWER
    }
    q = Question.objects.create(group=group, text=question['text'], kind=kinds[question['type']])
    choices = []
    for c in question['choices']:
        choices.append(Choice(question=q, text=c['text'], is_right=c['is_right']))
    Choice.objects.bulk_create(choices)

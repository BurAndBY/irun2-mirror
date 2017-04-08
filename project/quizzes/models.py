from django.db import models

from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible, smart_text


@python_2_unicode_compatible
class QuestionGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Question(models.Model):
    SINGLE_ANSWER = 0
    MULTIPLE_ANSWERS = 1
    TEXT_ANSWER = 2

    KIND_OF_CHOICES = (
        (SINGLE_ANSWER, _('Single correct answer')),
        (MULTIPLE_ANSWERS, _('Multiple correct answers')),
        (TEXT_ANSWER, _('Text answer')),
    )

    group = models.ForeignKey(QuestionGroup, on_delete=models.CASCADE)
    text = models.CharField(max_length=65535)
    is_deleted = models.BooleanField(default=False)
    kind = models.IntegerField(choices=KIND_OF_CHOICES, default=SINGLE_ANSWER)

    def __str__(self):
        return self.text


@python_2_unicode_compatible
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    is_right = models.BooleanField()

    def __str__(self):
        return self.text


@python_2_unicode_compatible
class QuizTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    shuffle_questions = models.BooleanField(default=True)
    question_groups = models.ManyToManyField(QuestionGroup, through='GroupQuizRelation')

    def __str__(self):
        return self.name


class GroupQuizRelation(models.Model):
    group = models.ForeignKey(QuestionGroup, on_delete=models.CASCADE)
    template = models.ForeignKey(QuizTemplate, on_delete=models.CASCADE)
    order = models.IntegerField(null=False)
    points = models.FloatField(default=1.)

    class Meta:
        ordering = ['order']

from __future__ import unicode_literals

from datetime import timedelta

from django.conf import settings
from django.db import models

from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible, smart_text

from courses.models import Course


@python_2_unicode_compatible
class Category(models.Model):
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('name for URL'), help_text=_('Short Latin name to use in page links'), unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Category')


@python_2_unicode_compatible
class QuestionGroup(models.Model):
    name = models.CharField(_('name'), max_length=100, unique=True)
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL, verbose_name=_('category'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Question group')


@python_2_unicode_compatible
class Question(models.Model):
    SINGLE_ANSWER = 0
    MULTIPLE_ANSWERS = 1
    TEXT_ANSWER = 2
    OPEN_ANSWER = 3

    KIND_OF_CHOICES = (
        (SINGLE_ANSWER, _('Single correct answer')),
        (MULTIPLE_ANSWERS, _('Multiple correct answers')),
        (TEXT_ANSWER, _('Text answer')),
        (OPEN_ANSWER, _('Open answer')),
    )

    group = models.ForeignKey(QuestionGroup, on_delete=models.CASCADE)
    text = models.CharField(max_length=16383)
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


class ScorePolicy(object):
    SOFT = 0
    STRICT = 1

    CHOICES = (
        (SOFT, _('soft')),
        (STRICT, _('strict')),
    )


@python_2_unicode_compatible
class QuizTemplate(models.Model):
    name = models.CharField(_('name'), max_length=100, unique=True)
    shuffle_questions = models.BooleanField(_('shuffle questions'), default=True)
    score_policy = models.IntegerField(_('score policy'), choices=ScorePolicy.CHOICES,
                                       default=ScorePolicy.STRICT)
    question_groups = models.ManyToManyField(QuestionGroup, through='GroupQuizRelation')
    attempts = models.IntegerField(_('attempts'), default=None, null=True, blank=True)
    time_limit = models.DurationField(_('time limit'), null=False, default=timedelta(minutes=30))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Quiz template')


class GroupQuizRelation(models.Model):
    group = models.ForeignKey(QuestionGroup, verbose_name=_('group'), on_delete=models.CASCADE)
    template = models.ForeignKey(QuizTemplate, on_delete=models.CASCADE)
    order = models.IntegerField(null=False)
    points = models.FloatField(_('points'), default=1.)

    class Meta:
        ordering = ['order']


@python_2_unicode_compatible
class QuizInstance(models.Model):
    quiz_template = models.ForeignKey(QuizTemplate, on_delete=models.CASCADE, verbose_name=_('quiz template'))
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name=_('course'))
    is_available = models.BooleanField(_('is available'), default=False)
    time_limit = models.DurationField(_('time limit'), null=False)
    tag = models.CharField(_('tag'), max_length=100, null=False, blank=True)
    attempts = models.IntegerField(_('attempts'), default=None, null=True, blank=True)
    show_answers = models.BooleanField(_('show answers'), default=True)
    enable_discussion = models.BooleanField(_('enable discussion'), default=False)

    def __str__(self):
        if self.tag:
            return '{} ({})'.format(self.quiz_template, self.tag)
        else:
            return smart_text(self.quiz_template)


@python_2_unicode_compatible
class QuizSession(models.Model):
    quiz_instance = models.ForeignKey(QuizInstance, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    score_policy = models.IntegerField(_('score policy'), choices=ScorePolicy.CHOICES,
                                       default=ScorePolicy.STRICT)
    start_time = models.DateTimeField()
    result = models.FloatField(default=0)
    is_finished = models.BooleanField(default=False)
    finish_time = models.DateTimeField(null=True)
    pending_manual_check = models.BooleanField(default=False)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+')

    def __str__(self):
        return '{}: {}'.format(self.quiz_instance, self.start_time)


@python_2_unicode_compatible
class SessionQuestion(models.Model):
    quiz_session = models.ForeignKey(QuizSession, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    order = models.IntegerField(null=False)
    points = models.FloatField(null=False)
    result_points = models.FloatField(null=False, default=0)

    def __str__(self):
        return smart_text(self.question)


@python_2_unicode_compatible
class SessionQuestionAnswer(models.Model):
    session_question = models.ForeignKey(SessionQuestion, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.PROTECT, null=True)
    user_answer = models.CharField(max_length=16383, default=None, null=True)
    is_chosen = models.BooleanField(default=False)

    def __str__(self):
        return smart_text(self.choice)


class AccessMode(object):
    READ = 1
    WRITE = 2

    CHOICES = (
        (READ, _('Read')),
        (WRITE, _('Write')),
    )


class CategoryAccess(models.Model):
    category = models.ForeignKey(Category)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    mode = models.IntegerField(choices=AccessMode.CHOICES)
    when_granted = models.DateTimeField(auto_now=True)
    who_granted = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', null=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('category', 'user')


class QuizSessionComment(models.Model):
    quiz_session = models.ForeignKey(QuizSession, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    text = models.CharField(max_length=16383, null=False)
    timestamp = models.DateTimeField()

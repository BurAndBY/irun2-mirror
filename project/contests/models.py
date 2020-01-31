# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from problems.models import Problem
from proglangs.models import Compiler
from solutions.models import Solution, Judgement
from solutions.permissions import SolutionAccessLevel
from storage.models import FileMetadata


class UnauthorizedAccessLevel(object):
    NO_ACCESS = 0
    VIEW_STANDINGS = 1
    VIEW_STANDINGS_AND_PROBLEMS = 2

    CHOICES = (
        (NO_ACCESS, _('No access')),
        (VIEW_STANDINGS, _('View standings')),
        (VIEW_STANDINGS_AND_PROBLEMS, _('View standings and problem statements')),
    )


class ContestKind(object):
    UNKNOWN = 0
    OFFICIAL = 1
    TRIAL = 2
    QUALIFYING = 3
    TRAINING = 4

    CHOICES = (
        (UNKNOWN, _('Not set')),
        (OFFICIAL, _('Official contest')),
        (TRIAL, _('Trial tour')),
        (QUALIFYING, _('Qualifying tour')),
        (TRAINING, _('Training')),
    )
    VALUE_TO_STRING = {k: v for k, v in CHOICES}


def _default_contest_start_time():
    ts = datetime.now() + timedelta(days=3)
    ts = ts.replace(hour=10, minute=0, second=0, microsecond=0)
    return ts


@python_2_unicode_compatible
class Contest(models.Model):
    ACM = 1
    IOI = 2

    RULES_CHOICES = (
        (ACM, 'ACM'),
        (IOI, 'IOI'),
    )

    name = models.CharField(_('name'), max_length=255)
    rules = models.IntegerField(_('rules'), choices=RULES_CHOICES, default=ACM)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Membership')
    compilers = models.ManyToManyField(Compiler, blank=True)
    problems = models.ManyToManyField(Problem, blank=True, through='ContestProblem')
    statements = models.ForeignKey(FileMetadata, null=True, on_delete=models.SET_NULL)
    unauthorized_access = models.IntegerField(_('access for unauthorized users'),
                                              choices=UnauthorizedAccessLevel.CHOICES, default=UnauthorizedAccessLevel.NO_ACCESS)
    contestant_own_solutions_access = models.IntegerField(_('contestant’s access to his own solutions'),
                                                          choices=SolutionAccessLevel.CHOICES, default=SolutionAccessLevel.TESTING_DETAILS_ON_SAMPLE_TESTS)
    attempt_limit = models.PositiveIntegerField(_('maximum number of attempts per problem'), default=100)
    file_size_limit = models.PositiveIntegerField(_('maximum solution file size (bytes)'), default=65536)
    start_time = models.DateTimeField(_('start time'), default=_default_contest_start_time)
    duration = models.DurationField(_('duration'), default=timedelta(hours=5))
    freeze_time = models.DurationField(_('standings freeze time'), null=True, blank=True, default=timedelta(hours=4), help_text=_('If not set, there will be no freezing.'))
    show_pending_runs = models.BooleanField(_('show pending runs during the freeze time'), blank=True, default=True)
    unfreeze_standings = models.BooleanField(_('unfreeze standings after the end of the contest'), blank=True, default=False)
    enable_upsolving = models.BooleanField(_('enable upsolving after the end of the contest'), blank=True, default=False)
    enable_printing = models.BooleanField(_('enable printing'), blank=True, default=False)
    rooms = models.CharField(_('rooms (comma-separated)'), blank=True, max_length=255)
    kind = models.IntegerField(_('kind'), choices=ContestKind.CHOICES, default=ContestKind.UNKNOWN)

    def get_absolute_url(self):
        return reverse('contests:standings', kwargs={'contest_id': self.pk})

    def __str__(self):
        return self.name

    def clean(self):
        if self.freeze_time is not None:
            if self.freeze_time > self.duration:
                raise ValidationError({'freeze_time': ValidationError(_('Freeze time must not exceed the contest duration.'))})

    def get_problems(self):
        return self.problems.order_by('link_to_contest')


class Membership(models.Model):
    CONTESTANT = 0
    JUROR = 1

    ROLE_CHOICES = (
        (CONTESTANT, _('contestant')),
        (JUROR, _('juror')),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contestmembership')
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    role = models.IntegerField(_('role'), choices=ROLE_CHOICES)


class ContestProblem(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='link_to_contest')
    ordinal_number = models.PositiveIntegerField()

    class Meta:
        ordering = ['ordinal_number']


class ContestSolution(models.Model):
    contest = models.ForeignKey(Contest, null=False, on_delete=models.CASCADE)
    solution = models.OneToOneField(Solution, null=False, on_delete=models.CASCADE)
    fixed_judgement = models.ForeignKey(Judgement, null=True, on_delete=models.SET_NULL)
    is_disqualified = models.BooleanField(default=False)


class Message(models.Model):
    QUESTION = 3
    ANSWER = 4
    MESSAGE = 5

    MESSAGE_TYPE_CHOICES = (
        (QUESTION, _('Question')),
        (ANSWER, _('Answer')),
        (MESSAGE, _('Message')),
    )

    message_type = models.IntegerField(choices=MESSAGE_TYPE_CHOICES)
    timestamp = models.DateTimeField()
    parent = models.ForeignKey('Message', null=True, on_delete=models.CASCADE, related_name='+')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, on_delete=models.PROTECT, related_name='+')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='+')
    subject = models.CharField(_('subject'), blank=False, null=True, max_length=255)
    text = models.TextField(_('message'), blank=False, max_length=65535)
    contest = models.ForeignKey(Contest, null=False, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, blank=True, null=True, on_delete=models.PROTECT, related_name='+')
    is_answered = models.BooleanField(default=False)


class MessageUser(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('message', 'user')


class Printout(models.Model):
    DONE = 0
    WAITING = 1
    PRINTING = 2
    CANCELLED = 3

    STATUS_CHOICES = (
        (DONE, _('Done')),
        (WAITING, _('Waiting')),
        (PRINTING, _('Printing')),
        (CANCELLED, _('Cancelled')),
    )

    contest = models.ForeignKey(Contest, null=False, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, on_delete=models.PROTECT, related_name='+')
    room = models.CharField(_('room'), blank=False, max_length=64)
    timestamp = models.DateTimeField()
    text = models.TextField(_('text'), blank=False, max_length=65535)
    status = models.IntegerField(_('status'), default=WAITING, choices=STATUS_CHOICES)


class ContestUserRoom(models.Model):
    contest = models.ForeignKey(Contest, null=False, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, on_delete=models.PROTECT, related_name='+')
    room = models.CharField(_('room'), blank=True, max_length=64)

    class Meta:
        unique_together = ('contest', 'user')


class UserFilter(models.Model):
    contest = models.ForeignKey(Contest, null=False, on_delete=models.CASCADE)
    name = models.CharField(_('name'), blank=False, max_length=255)
    regex = models.CharField(_('regular expression'), blank=False, max_length=255)

from django.db import models
from django.utils.translation import ugettext_lazy as _

from problems.models import ProblemFolder
from proglangs.models import Compiler


class Criterion(models.Model):
    label = models.CharField(max_length=8)
    name = models.CharField(max_length=64)


class Course(models.Model):
    name = models.CharField(_('name'), max_length=64)
    compilers = models.ManyToManyField(Compiler, blank=True)


class Topic(models.Model):
    name = models.CharField(_('name'), max_length=64)
    course = models.ForeignKey(Course, null=False, on_delete=models.CASCADE)
    problem_folder = models.ForeignKey(ProblemFolder, null=True, on_delete=models.SET_NULL, verbose_name=_('problem folder'))
    criteria = models.ManyToManyField(Criterion, blank=True, verbose_name=_('criteria'))


class Slot(models.Model):
    topic = models.ForeignKey(Topic, null=False, on_delete=models.CASCADE)


class Activity(models.Model):
    PROBLEM_SOLVING = 0
    MARK = 1
    PASSED_OR_NOT = 2

    KIND_CHOICES = (
        (PROBLEM_SOLVING, _('solving problems within the course')),
        (MARK, _('mark')),
        (PASSED_OR_NOT, _('passed or not passed'))
    )

    course = models.ForeignKey(Course)
    name = models.CharField(_('name'), max_length=64)
    kind = models.IntegerField(_('kind'), choices=KIND_CHOICES)
    weight = models.FloatField(_('weight'), default=0.0)

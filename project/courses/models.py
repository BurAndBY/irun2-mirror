from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from problems.models import ProblemFolder, Problem
from proglangs.models import Compiler
from django.core.urlresolvers import reverse


class Criterion(models.Model):
    label = models.CharField(max_length=8)
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(_('name'), max_length=64)
    compilers = models.ManyToManyField(Compiler, blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Membership')

    def get_absolute_url(self):
        return reverse('courses:show_course_info', kwargs={'course_id': self.id})


class Topic(models.Model):
    name = models.CharField(_('name'), max_length=64)
    course = models.ForeignKey(Course, null=False, on_delete=models.CASCADE)
    problem_folder = models.ForeignKey(ProblemFolder, null=True, on_delete=models.SET_NULL, verbose_name=_('problem folder'))
    criteria = models.ManyToManyField(Criterion, blank=True, verbose_name=_('criteria'))

    def __unicode__(self):
        return self.name

    def list_problems(self):
        problems = []
        if self.problem_folder is not None:
            problems = self.problem_folder.problem_set.all().order_by('number', 'subnumber')
        return problems


class Slot(models.Model):
    topic = models.ForeignKey(Topic, null=False, on_delete=models.CASCADE)


class Activity(models.Model):
    PROBLEM_SOLVING = 0
    MARK = 1
    PASSED_OR_NOT = 2

    KIND_CHOICES = (
        (PROBLEM_SOLVING, _('solving problems within the course')),
        (MARK, _('mark')),
        (PASSED_OR_NOT, _('passed or not passed')),
    )

    course = models.ForeignKey(Course)
    name = models.CharField(_('name'), max_length=64)
    kind = models.IntegerField(_('kind'), choices=KIND_CHOICES)
    weight = models.FloatField(_('weight'), default=0.0)


class Membership(models.Model):
    STUDENT = 0
    TEACHER = 1

    ROLE_CHOICES = (
        (STUDENT, _('student')),
        (TEACHER, _('teacher')),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    course = models.ForeignKey(Course)
    role = models.IntegerField(_('role'), choices=ROLE_CHOICES)


class Assignment(models.Model):
    slot = models.ForeignKey(Slot, null=True, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, null=True, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, null=True, blank=True, on_delete=models.CASCADE, verbose_name=_('problem'))
    membership = models.ForeignKey(Membership, null=False, on_delete=models.CASCADE)
    criteria = models.ManyToManyField(Criterion, blank=True, verbose_name=_('criteria'))
    extra_requirements = models.TextField(max_length=1024, blank=True)
    extra_requirements_ok = models.BooleanField(blank=True, default=False)
    bonus_attempts = models.IntegerField(default=0)

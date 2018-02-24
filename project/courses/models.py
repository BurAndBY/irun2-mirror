# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

from problems.models import ProblemFolder, Problem
from proglangs.models import Compiler
from solutions.models import Solution
from solutions.permissions import SolutionAccessLevel
from storage.models import FileMetadata

from courses.utils import make_year_of_study_string, make_academic_year_string


class Criterion(models.Model):
    label = models.CharField(_('criterion label'), max_length=8, unique=True)
    name = models.CharField(_('name'), max_length=64)

    def __unicode__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(_('name'), max_length=64, blank=True)
    compilers = models.ManyToManyField(Compiler, blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Membership')

    student_own_solutions_access = models.IntegerField(_(u'student’s access to his own solutions'),
                                                       choices=SolutionAccessLevel.CHOICES, default=SolutionAccessLevel.TESTING_DETAILS)

    student_all_solutions_access = models.IntegerField(_(u'student’s access to all solutions of the course'),
                                                       choices=SolutionAccessLevel.CHOICES, default=SolutionAccessLevel.STATE)

    enable_sheet = models.BooleanField(_('enable mark sheet'), default=False, blank=True)
    enable_queues = models.BooleanField(_('enable electronic queues'), default=False, blank=True)

    common_problems = models.ManyToManyField(Problem, blank=True)

    attempts_a_day = models.PositiveIntegerField(_('Number of attempts a day per problem'), null=True, blank=True, default=5)

    year_of_study = models.PositiveIntegerField(_('Year of study'), null=True, blank=True)
    group = models.PositiveIntegerField(_('Group number'), null=True, blank=True)
    academic_year = models.PositiveIntegerField(_('Academic year'), null=True, blank=True)

    def get_absolute_url(self):
        return reverse('courses:show_course_info', kwargs={'course_id': self.id})

    def clean(self):
        if (len(self.name) == 0) and (self.year_of_study is None) and (self.group is None) and (self.academic_year is None):
            raise ValidationError(_('No information is given to identify the course.'))

    def __unicode__(self):
        tokens = []
        if self.year_of_study is not None:
            tokens.append(make_year_of_study_string(self.year_of_study))
        if self.group is not None:
            tokens.append(ugettext(u'%(group)d group') % {'group': self.group})
        if len(self.name) > 0:
            tokens.append(self.name)
        if self.academic_year is not None:
            tokens.append(make_academic_year_string(self.academic_year))
        if len(tokens) == 0:
            tokens.append('<...>')
        return u' '.join(tokens)

    class Meta:
        ordering = ['academic_year', 'year_of_study', 'group', 'name']


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
    QUIZ_RESULT = 3

    KIND_CHOICES = (
        (PROBLEM_SOLVING, _('solving problems within the course')),
        (MARK, _('mark')),
        (PASSED_OR_NOT, _('passed or not passed')),
        (QUIZ_RESULT, _('quiz result')),
    )

    course = models.ForeignKey(Course)
    name = models.CharField(_('name'), max_length=64)
    description = models.TextField(_('description'), blank=True, max_length=255)
    kind = models.IntegerField(_('kind'), choices=KIND_CHOICES)
    weight = models.FloatField(_('weight'), default=0.0)
    quiz_instance = models.ForeignKey('quizzes.QuizInstance', verbose_name=_('quiz'), null=True, blank=True, on_delete=models.SET_NULL)


class Subgroup(models.Model):
    course = models.ForeignKey(Course)
    name = models.CharField(_('name'), max_length=16, blank=False)

    def __unicode__(self):
        return self.name


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
    subgroup = models.ForeignKey(Subgroup, verbose_name=_('subgroup'), null=True, blank=True, on_delete=models.SET_NULL)


class Assignment(models.Model):
    slot = models.ForeignKey(Slot, null=True, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, null=True, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, null=True, blank=True, on_delete=models.CASCADE, verbose_name=_('problem'))
    membership = models.ForeignKey(Membership, null=False, on_delete=models.CASCADE)
    criteria = models.ManyToManyField(Criterion, blank=True, verbose_name=_('criteria'))
    extra_requirements = models.TextField(max_length=1024, blank=True)
    extra_requirements_ok = models.BooleanField(blank=True, default=False)
    bonus_attempts = models.IntegerField(default=0)


class AssignmentCriteriaIntermediate(models.Model):
    '''
    This model is used to get direct access to many-to-many relation.
    '''
    assignment = models.ForeignKey(Assignment)
    criterion = models.ForeignKey(Criterion)

    class Meta:
        managed = False
        db_table = 'courses_assignment_criteria'


class CourseSolution(models.Model):
    course = models.ForeignKey(Course, null=False, on_delete=models.CASCADE)
    solution = models.OneToOneField(Solution, null=False, on_delete=models.CASCADE)


class ActivityRecord(models.Model):
    UNDEFINED = 0
    PASS = 1
    NO_PASS = 2
    ABSENCE = 3

    CHOICES = (
        (UNDEFINED, ''),
        (PASS, _('pass')),
        (NO_PASS, _('no pass')),
        (ABSENCE, _('absence')),
    )

    membership = models.ForeignKey(Membership, null=False, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, null=False, on_delete=models.CASCADE)
    mark = models.IntegerField(null=False, default=0)
    enum = models.IntegerField(null=False, choices=CHOICES, default=UNDEFINED)


'''
Messaging
'''


class MailThread(models.Model):
    course = models.ForeignKey(Course)
    subject = models.CharField(_('subject'), blank=True, max_length=255)
    problem = models.ForeignKey(Problem, null=True)
    person = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    last_message_timestamp = models.DateTimeField()
    resolved = models.BooleanField(blank=True, default=True)


class MailMessage(models.Model):
    thread = models.ForeignKey(MailThread)
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    timestamp = models.DateTimeField()
    body = models.TextField(_('message'), max_length=65535)
    attachment = models.ForeignKey(FileMetadata, null=True, on_delete=models.SET_NULL, verbose_name=_('attachment'))


class MailUserThreadVisit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    thread = models.ForeignKey(MailThread)
    timestamp = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'thread')


'''
Electronic Queues
'''


@python_2_unicode_compatible
class Queue(models.Model):
    course = models.ForeignKey(Course)
    is_active = models.BooleanField(_('queue is active'), blank=True, default=True)
    name = models.CharField(_('name'), blank=True, max_length=255)
    subgroup = models.ForeignKey(Subgroup, verbose_name=_('subgroup'), null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        if self.name:
            return self.name
        return ugettext('Queue')


class QueueEntryStatus(object):
    WAITING = 0
    IN_PROGRESS = 1
    DONE = 2

    CHOICES = (
        (WAITING, _('Waiting')),
        (IN_PROGRESS, _('In progress')),
        (DONE, _('Done')),
    )


class QueueEntry(models.Model):
    queue = models.ForeignKey(Queue)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    status = models.IntegerField(_('status'), choices=QueueEntryStatus.CHOICES, default=QueueEntryStatus.WAITING)

    enqueue_time = models.DateTimeField(_('enqueue time'), null=False)
    start_time = models.DateTimeField(null=True)
    finish_time = models.DateTimeField(null=True)

from django.db import models
from storage.storage import ResourceIdField
from proglangs.models import Compiler
from problems.models import Problem
from django.utils.translation import ugettext as _


class AdHocRun(models.Model):
    resource_id = ResourceIdField()
    input_file_name = models.CharField(max_length=80, blank=True)
    output_file_name = models.CharField(max_length=80, blank=True)

    time_limit = models.IntegerField(default=10000)
    memory_limit = models.IntegerField(default=0)


class Solution(models.Model):
    problem = models.ForeignKey(Problem, null=True, on_delete=models.SET_NULL)
    ad_hoc_run = models.ForeignKey(AdHocRun, null=True, on_delete=models.SET_NULL)

    filename = models.CharField(max_length=256, blank=True)
    resource_id = ResourceIdField()
    programming_language = models.ForeignKey(Compiler)

    best_judgement = models.ForeignKey('Judgement', null=True, related_name='+')


class Outcome(object):
    NOT_AVAILABLE = 0
    ACCEPTED = 1
    COMPILATION_ERROR = 2
    WRONG_ANSWER = 3
    TIME_LIMIT_EXCEEDED = 4
    MEMORY_LIMIT_EXCEEDED = 5
    IDLENESS_LIMIT_EXCEEDED = 6
    RUNTIME_ERROR = 7
    PRESENTATION_ERROR = 8
    SECURITY_VIOLATION = 9
    CHECK_FAILED = 10

    CHOICES = (
        (NOT_AVAILABLE, _('N/A')),
        (ACCEPTED, _('Accepted')),
        (COMPILATION_ERROR, _('Compilation Error')),
        (WRONG_ANSWER, _('Wrong Answer')),
        (TIME_LIMIT_EXCEEDED, _('Time Limit Exceeded')),
        (MEMORY_LIMIT_EXCEEDED, _('Memory Limit Exceeded')),
        (IDLENESS_LIMIT_EXCEEDED, _('Idleness Limit Exceeded')),
        (RUNTIME_ERROR, _('Runtime Error')),
        (PRESENTATION_ERROR, _('Presentation Error')),
        (SECURITY_VIOLATION, _('Security Violation')),
        (CHECK_FAILED, _('Check Failed'))
    )


class Judgement(models.Model):
    DONE = 0
    WAITING = 1
    PREPARING = 2
    COMPILING = 3
    TESTING = 4
    FINISHING = 5

    STATUS_CHOICES = (
        (DONE, _('Done')),
        (WAITING, _('Waiting')),
        (PREPARING, _('Preparing')),
        (COMPILING, _('Compiling')),
        (TESTING, _('Testing')),
        (FINISHING, _('Finishing')),
    )

    solution = models.ForeignKey(Solution)

    compilation_log = ResourceIdField()

    status = models.IntegerField(default=DONE, choices=STATUS_CHOICES)
    outcome = models.IntegerField(default=Outcome.NOT_AVAILABLE, choices=Outcome.CHOICES)
    is_accepted = models.BooleanField(default=False)

    score = models.IntegerField(default=0)
    max_score = models.IntegerField(default=0)

    general_failure_reason = models.IntegerField(default=0)
    general_failure_message = models.CharField(max_length=255)


class TestCaseResult(models.Model):
    judgement = models.ForeignKey(Judgement)

    input_resource_id = ResourceIdField(null=True)
    output_resource_id = ResourceIdField(null=True)
    answer_resource_id = ResourceIdField(null=True)
    stdout_resource_id = ResourceIdField(null=True)
    stderr_resource_id = ResourceIdField(null=True)

    exit_code = models.IntegerField()

    time_limit = models.IntegerField(null=True)
    time_used = models.IntegerField()

    memory_limit = models.IntegerField(null=True)
    memory_used = models.IntegerField()

    score = models.IntegerField()
    max_score = models.IntegerField()

    checker_message = models.CharField(max_length=255, blank=True)

    outcome = models.IntegerField()

from django.db import models
from storage.storage import ResourceIdField
from proglangs.models import Compiler
from problems.models import Problem, TestCase
from django.utils.translation import ugettext_lazy as _


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
    compiler = models.ForeignKey(Compiler)

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


class Rejudge(models.Model):
    committed = models.NullBooleanField()


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
    rejudge = models.ForeignKey(Rejudge, null=True, on_delete=models.SET_NULL, default=None)

    status = models.IntegerField(default=WAITING, choices=STATUS_CHOICES)
    outcome = models.IntegerField(default=Outcome.NOT_AVAILABLE, choices=Outcome.CHOICES)
    test_number = models.IntegerField(default=0)

    score = models.IntegerField(default=0)
    max_score = models.IntegerField(default=0)

    general_failure_reason = models.IntegerField(default=0)
    general_failure_message = models.CharField(max_length=255)

    def show_status(self):
        if self.status != Judgement.DONE:
            result = self.get_status_display()
        else:
            result = self.get_outcome_display()
            if self.test_number != 0:
                result += ' ({0})'.format(self.test_number)
        return result


class JudgementLog(models.Model):
    COMPILATION = 0

    LOG_KIND_CHOICES = (
        (COMPILATION, _('Compilation log')),
    )

    judgement = models.ForeignKey(Judgement)
    resource_id = ResourceIdField()
    kind = models.IntegerField(default=COMPILATION, choices=LOG_KIND_CHOICES)


class TestCaseResult(models.Model):
    judgement = models.ForeignKey(Judgement)

    test_case = models.ForeignKey(TestCase, null=True, on_delete=models.SET_NULL)

    input_resource_id = ResourceIdField(null=True)
    output_resource_id = ResourceIdField(null=True)
    answer_resource_id = ResourceIdField(null=True)
    stdout_resource_id = ResourceIdField(null=True)
    stderr_resource_id = ResourceIdField(null=True)

    exit_code = models.IntegerField()

    time_limit = models.IntegerField(default=0)
    time_used = models.IntegerField()

    memory_limit = models.IntegerField(default=0)
    memory_used = models.IntegerField()

    score = models.IntegerField()
    max_score = models.IntegerField()

    checker_message = models.CharField(max_length=255, blank=True)

    outcome = models.IntegerField(default=Outcome.NOT_AVAILABLE, choices=Outcome.CHOICES)

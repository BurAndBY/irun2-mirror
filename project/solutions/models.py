from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from common.constants import ACCEPTED_FOR_TESTING
from common.outcome import Outcome
from problems.models import Problem, TestCase
from proglangs.models import Compiler
from storage.models import FileMetadata
from storage.storage import ResourceIdField


class AdHocRun(models.Model):
    resource_id = ResourceIdField()
    input_file_name = models.CharField(max_length=80, blank=True)
    output_file_name = models.CharField(max_length=80, blank=True)

    time_limit = models.IntegerField(default=10000)
    memory_limit = models.IntegerField(default=0)


class Solution(models.Model):
    problem = models.ForeignKey(Problem)
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    reception_time = models.DateTimeField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    source_code = models.ForeignKey(FileMetadata)
    compiler = models.ForeignKey(Compiler)
    stop_on_fail = models.BooleanField(default=False)

    best_judgement = models.ForeignKey('Judgement', null=True, related_name='+')  # '+' means 'do not create a backwards relation'


class Rejudge(models.Model):
    committed = models.NullBooleanField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, on_delete=models.PROTECT)
    creation_time = models.DateTimeField(auto_now_add=True)


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
    judgement_before = models.ForeignKey('Judgement', null=True, on_delete=models.SET_NULL, default=None, related_name='+')

    status = models.IntegerField(default=WAITING, choices=STATUS_CHOICES)
    outcome = models.IntegerField(default=Outcome.NOT_AVAILABLE, choices=Outcome.CHOICES)
    test_number = models.IntegerField(default=0)

    score = models.IntegerField(default=0)
    max_score = models.IntegerField(default=0)

    sample_tests_passed = models.NullBooleanField(default=None)

    def show_status(self, complete=True):
        '''
        If complete is False, we show sample results only.
        '''
        if self.status != Judgement.DONE:
            result = self.get_status_display()
        else:
            if (complete) or (self.sample_tests_passed is False):
                result = self.get_outcome_display()
            else:
                result = ACCEPTED_FOR_TESTING

        test = self.test_number

        if not complete:
            if not (self.status == Judgement.DONE and self.sample_tests_passed is False):
                # hide number of tests
                test = 0

        if test != 0:
            result += ' ({0})'.format(test)
        return result


class JudgementExtraInfo(models.Model):
    judgement = models.OneToOneField(Judgement, on_delete=models.CASCADE, primary_key=True, related_name='extra_info')

    creation_time = models.DateTimeField(null=True)
    start_testing_time = models.DateTimeField(null=True)
    finish_testing_time = models.DateTimeField(null=True)

    general_failure_reason = models.CharField(max_length=64, default='')  # contains uppercase enum values
    general_failure_message = models.CharField(max_length=255, default='')


class JudgementLog(models.Model):
    SOLUTION_COMPILATION = 0

    LOG_KIND_CHOICES = (
        (SOLUTION_COMPILATION, _('Solution compilation log')),
    )

    judgement = models.ForeignKey(Judgement)
    resource_id = ResourceIdField()
    kind = models.IntegerField(default=SOLUTION_COMPILATION, choices=LOG_KIND_CHOICES)


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

    memory_limit = models.BigIntegerField(default=0)
    memory_used = models.BigIntegerField()

    score = models.IntegerField()
    max_score = models.IntegerField()

    checker_message = models.CharField(max_length=255, blank=True)

    outcome = models.IntegerField(default=Outcome.NOT_AVAILABLE, choices=Outcome.CHOICES)

    is_sample = models.BooleanField(default=False)


class Challenge(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, on_delete=models.PROTECT)
    creation_time = models.DateTimeField(auto_now_add=True)

    problem = models.ForeignKey(Problem)
    time_limit = models.IntegerField()
    memory_limit = models.IntegerField(default=0)

    input_resource_id = ResourceIdField()


class ChallengedSolution(models.Model):
    challenge = models.ForeignKey(Challenge)
    solution = models.ForeignKey(Solution)

    outcome = models.IntegerField(default=Outcome.NOT_AVAILABLE, choices=Outcome.CHOICES)
    output_resource_id = ResourceIdField(null=True)
    stdout_resource_id = ResourceIdField(null=True)
    stderr_resource_id = ResourceIdField(null=True)
    exit_code = models.IntegerField(null=True)
    time_used = models.IntegerField(null=True)
    memory_used = models.IntegerField(null=True)

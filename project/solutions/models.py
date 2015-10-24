from django.db import models
from storage.storage import ResourceIdField
from proglangs.models import ProgrammingLanguage
from problems.models import Problem


class Solution(models.Model):
    filename = models.CharField(max_length=256, blank=True)
    handle = ResourceIdField()
    programming_language = models.ForeignKey(ProgrammingLanguage)


class SimpleTest(models.Model):
    handle = ResourceIdField()
    input_file_name = models.CharField(max_length=80, blank=True)
    output_file_name = models.CharField(max_length=80, blank=True)

    time_limit = models.IntegerField(default=10000)
    memory_limit = models.IntegerField(default=0)


class Outcome(object):
    NOT_AVAILABLE = 0

    OK = 1
    TIME_LIMIT_EXCEEDED = 2
    MEMORY_LIMIT_EXCEEDED = 3
    IDLENESS_LIMIT_EXCEEDED = 4
    RUNTIME_ERROR = 5
    SECURITY_VIOLATION = 6

    WRONG_ANSWER = 7
    PRESENTATION_ERROR = 8
    CHECK_FAILED = 9

    SOLUTION_COMPILATION_ERROR = 10
    CHECKER_COMPILATION_ERROR = 11
    GENERAL_FAILURE = 12


class GeneralFailureReason(object):
    pass


class Judgement(models.Model):
    solution = models.ForeignKey(Solution)
    problem = models.ForeignKey(Problem, null=True)
    simple_test = models.ForeignKey(SimpleTest, null=True)

    compilation_log = ResourceIdField()

    score = models.IntegerField()
    max_score = models.IntegerField()

    outcome = models.IntegerField()
    is_accepted = models.BooleanField()

    general_failure_reason = models.IntegerField()
    general_failure_message = models.CharField(max_length=255)


class TestCaseResult(models.Model):
    judgement = models.ForeignKey(Judgement)

    input_handle = ResourceIdField()
    output_handle = ResourceIdField()
    answer_handle = ResourceIdField()
    stdout_handle = ResourceIdField()
    stderr_handle = ResourceIdField()

    exit_code = models.IntegerField()

    time_limit = models.IntegerField(null=True)
    time_used = models.IntegerField()

    memory_limit = models.IntegerField(null=True)
    memory_used = models.IntegerField()

    score = models.IntegerField()
    max_score = models.IntegerField()

    checker_message = models.CharField(max_length=255, blank=True)

    outcome = models.IntegerField()
    check_failed_reason = models.IntegerField()

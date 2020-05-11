from collections import namedtuple
from enum import Enum


class CheckFailed(Exception):
    pass


class Outcome(Enum):
    NOT_AVAILABLE = 0
    ACCEPTED = 1
    FAILED = 2
    CHECK_FAILED = 3
    TIME_LIMIT_EXCEEDED = 4
    COMPILATION_ERROR = 5


TestCaseResult = namedtuple('TestCaseResult', ['test_case', 'outcome', 'time_used', 'time_limit', 'message', 'traceback', 'stdout', 'stderr'])


class TestCase:
    def __init__(self):
        self.test_case_id = None
        self.input_resource_id = None
        self.answer_resource_id = None


class TestingJob:
    def __init__(self, job_id):
        self.job_id = job_id
        self.solution_resource_id = None
        self.solution_compiler = None
        self.checker_resource_id = None
        self.default_time_limit = 1000
        self.solution_filename = 'solution'
        self.test_cases = []


class TestingReport:
    def __init__(self):
        self.outcome = Outcome.NOT_AVAILABLE
        self.first_failed_test = 0
        self.compilation_log = None
        self.tests = []

    @staticmethod
    def check_failed():
        report = TestingReport()
        report.outcome = Outcome.CHECK_FAILED
        return report

    @staticmethod
    def compilation_error(log):
        report = TestingReport()
        report.outcome = Outcome.COMPILATION_ERROR
        report.compilation_log = log
        return report

    @staticmethod
    def from_tests(tests, log):
        report = TestingReport()
        report.outcome = Outcome.ACCEPTED
        report.compilation_log = log
        report.tests = tests
        for test in tests:
            if test.outcome != Outcome.ACCEPTED and report.outcome == Outcome.ACCEPTED:
                report.outcome = test.outcome
        return report


class ITester:
    def run(self, job):
        raise NotImplementedError()


class IStateCallback:
    def set_compiling(self):
        pass

    def set_testing(self):
        pass

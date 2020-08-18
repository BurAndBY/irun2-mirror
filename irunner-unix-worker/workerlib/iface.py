from collections import namedtuple
from enum import Enum
from json import load as json_load, JSONDecodeError


class CheckFailed(Exception):
    def __init__(self, message=''):
        self.message = message


class Outcome(Enum):
    NOT_AVAILABLE = 0
    ACCEPTED = 1
    FAILED = 2
    CHECK_FAILED = 3
    TIME_LIMIT_EXCEEDED = 4
    COMPILATION_ERROR = 5


TestCaseResult = namedtuple(
    'TestCaseResult',
    ['test_case', 'outcome', 'score', 'max_score', 'time_used', 'time_limit',
     'message', 'traceback', 'stdout', 'stderr'])

LibraryFile = namedtuple('LibraryFile', ['resource_id', 'filename', 'compiler'])


class TestCase:
    def __init__(self):
        self.test_case_id = None
        self.input_resource_id = None
        self.answer_resource_id = None


class TestingJob:
    PYTEST = 'PYTEST'
    GTEST = 'GTEST'

    def __init__(self, job_id):
        self.job_id = job_id
        self.solution_resource_id = None
        self.solution_compiler = None
        self.checker_resource_id = None
        self.checker_kind = None
        self.libraries = []
        self.default_time_limit = 1000
        self.solution_filename = 'solution'
        self.test_cases = []


class TestingReport:
    def __init__(self):
        self.outcome = Outcome.NOT_AVAILABLE
        self.score = None
        self.max_score = None
        self.first_failed_test = None
        self.compilation_log = None
        self.tests = []

    @staticmethod
    def check_failed(log):
        report = TestingReport()
        report.outcome = Outcome.CHECK_FAILED
        report.compilation_log = log
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

    @staticmethod
    def from_json(job, compilation_log, test_results):
        try:
            with open(test_results, 'r') as json_file:
                data = json_load(json_file)
        except (IOError, JSONDecodeError):
            raise CheckFailed('Unable to parse report JSON')

        report = TestingReport()
        report.compilation_log = compilation_log
        report.first_failed_test = 0

        if data['verdict'] == 'ACCEPTED':
            report.outcome = Outcome.ACCEPTED
        else:
            report.outcome = Outcome.FAILED

        report.score = data['score']
        report.max_score = data['max_score']

        for test in data['tests']:
            report.tests.append(TestCaseResult(
                None,
                Outcome.ACCEPTED if test['verdict'] else Outcome.FAILED,
                test['score'],
                test['max_score'],
                test['time_ms'],
                test['time_limit_ms'],
                test['comment'],
                test['output'],
                test['stdout'],
                test['stderr'],
            ))

        return report


class ITester:
    def run(self, job):
        raise NotImplementedError()


class IStateCallback:
    def set_compiling(self):
        pass

    def set_testing(self):
        pass

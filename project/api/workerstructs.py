class WorkerFile(object):
    def __init__(self, resource_id):
        self.resource_id = resource_id


class WorkerTestCase(object):
    def __init__(self, test_id):
        self.id = test_id
        self.input = None
        self.answer = None
        self.time_limit = 0
        self.memory_limit = 0
        self.max_score = 0
        self.is_sample = False


class WorkerProblem(object):
    def __init__(self, problem_id):
        self.id = problem_id
        self.name = ''
        self.input_file_name = ''
        self.output_file_name = ''
        self.tests = []
        self.checker = None
        self.validator = None


class WorkerTestingJob(object):
    def __init__(self, job_id=None):
        self.id = job_id
        self.problem = None
        self.solution = None
        self.stop_after_first_failed_test = False


class WorkerTestingReport(object):
    def __init__(self, outcome, first_failed_test, tests, score, max_score, logs, general_failure_reason, general_failure_message, sample_tests_passed):
        self.outcome = outcome
        self.first_failed_test = first_failed_test
        self.tests = tests
        self.score = score
        self.max_score = max_score
        self.logs = logs
        self.general_failure_reason = general_failure_reason
        self.general_failure_message = general_failure_message
        self.sample_tests_passed = sample_tests_passed


class WorkerState(object):
    def __init__(self, status, test_number=0):
        self.status = status
        self.test_number = test_number


class WorkerChecker(object):
    IRUNNER = 'IRUNNER'
    ACCEPT_ALL = 'ACCEPT_ALL'

    def __init__(self, source=None):
        self.source = source
        self.kind = self.IRUNNER


class WorkerValidator(object):
    def __init__(self):
        self.source = None


class WorkerGreeting(object):
    def __init__(self, name):
        self.name = name

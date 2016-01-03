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


class WorkerProblem(object):
    def __init__(self, problem_id):
        self.id = problem_id
        self.name = ''
        self.input_file_name = ''
        self.output_file_name = ''
        self.tests = []


class WorkerTestingJob(object):
    def __init__(self, job_id):
        self.id = job_id
        self.problem = None
        self.solution = None
        self.stop_after_first_failed_test = False


class WorkerTestingReport(object):
    def __init__(self, outcome, first_failed_test, tests, score, max_score, logs):
        self.outcome = outcome
        self.first_failed_test = first_failed_test
        self.tests = tests
        self.score = score
        self.max_score = max_score
        self.logs = logs


class WorkerState(object):
    def __init__(self, status, test_number):
        self.status = status
        self.test_number = test_number

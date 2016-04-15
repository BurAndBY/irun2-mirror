class PlagiarismSubJob(object):
    def __init__(self, id, resource_id):
        self.id = id
        self.resource_id = resource_id

class PlagiarismTestingJob(object):
    def __init__(self, solution, solutions):
        self.solution = solution
        self.solutions = solutions
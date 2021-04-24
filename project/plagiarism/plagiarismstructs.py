class PlagiarismSubJob(object):
    def __init__(self, id, language, resource_id):
        self.id = id
        self.language = language
        self.resource_id = resource_id

class PlagiarismTestingJob(object):
    def __init__(self, solution, solutions):
        self.solution = solution
        self.solutions = solutions

class SolutionPermissions(object):
    def __init__(self):
        self.tests_data = True
        self.checker_messages = True
        self.source_code = True
        self.compilation_log = True
        self.results = True

    @staticmethod
    def all():
        return SolutionPermissions()

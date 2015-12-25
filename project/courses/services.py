from collections import namedtuple


class ProblemResult(object):
    def __init__(self, points, max_points):
        self.points = points
        self.max_points = max_points

    def is_full_solution(self):
        return self.points == self.max_points


class ProblemResultsManager(object):
    def __init__(self):
        pass

    def get(self, user_id, problem_id):
        return None

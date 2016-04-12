from collections import namedtuple

from solutions.permissions import SolutionAccessLevel


class ContestPermissions(object):
    def __init__(self):
        self.standings = False
        self.standings_before = False
        self.always_unfrozen_standings = False
        self.problems = False
        self.problems_before = False
        self.all_solutions = False
        self.my_solutions = False
        self.submit = False
        self.submit_always = False
        self.settings = False

    def set_juror(self):
        self.standings = True
        self.standings_before = True
        self.always_unfrozen_standings = True
        self.problems = True
        self.problems_before = True
        self.settings = True
        self.all_solutions = True
        self.submit = True
        self.submit_always = True

    def set_contestant(self, own_solutions_access):
        self.standings = True
        self.problems = True
        self.my_solutions |= (own_solutions_access != SolutionAccessLevel.NO_ACCESS)
        self.submit = True

    def set_admin(self):
        self.set_juror()

InContestAccessLevel = namedtuple('InContestAccessLevel', 'contest level')

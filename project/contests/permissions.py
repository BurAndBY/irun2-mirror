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
        self.read_messages = False
        self.manage_messages = False
        self.ask_questions = False
        self.answer_questions = False
        self.compilers = False
        self.export = False
        self.printing = False
        self.manage_printing = False

    def set_juror(self):
        self.standings = True
        self.always_unfrozen_standings = True
        self.problems = True
        self.all_solutions = True
        self.submit = True
        self.manage_messages = True
        self.answer_questions = True
        self.compilers = True
        self.printing = True
        self.manage_printing = True

    def set_contestant(self, own_solutions_access):
        self.standings = True
        self.problems = True
        self.my_solutions |= (own_solutions_access != SolutionAccessLevel.NO_ACCESS)
        self.submit = True
        self.read_messages = True
        self.ask_questions = True
        self.compilers = True
        self.printing = True

    def set_admin(self):
        self.set_juror()
        self.standings_before = True
        self.problems_before = True
        self.submit_always = True
        self.settings = True
        self.export = True

    def disable_printing(self):
        self.printing = False
        self.manage_printing = False

InContestAccessLevel = namedtuple('InContestAccessLevel', 'contest level samples_only_state')

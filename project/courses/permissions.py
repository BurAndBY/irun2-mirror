from solutions.permissions import SolutionAccessLevel


class CoursePermissions(object):
    def __init__(self):
        self.info = False
        self.problems = False
        self.my_problems = False
        self.standings = False
        self.sheet = False
        self.sheet_edit = False
        self.submit = False
        self.submit_all_problems = False
        self.settings = False
        self.assign = False
        self.my_solutions = False
        self.all_solutions = False

    def set_common(self):
        self.info = True
        self.problems = True
        self.standings = True
        self.sheet = True

    def set_student(self, own_solutions_access, all_solutions_access):
        self.set_common()

        self.submit = True
        self.my_problems = True
        self.my_solutions |= (own_solutions_access != SolutionAccessLevel.NO_ACCESS)
        self.all_solutions |= (all_solutions_access != SolutionAccessLevel.NO_ACCESS)

    def set_teacher(self):
        self.set_common()

        self.submit = True
        self.submit_all_problems = True
        self.sheet_edit = True
        self.assign = True
        self.my_solutions = True
        self.all_solutions = True

    def set_admin(self):
        self.set_common()

        self.settings = True

    def disable_sheet(self):
        self.sheet = False
        self.sheet_edit = False

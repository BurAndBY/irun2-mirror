from collections import namedtuple

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
        self.editorials = False
        self.settings = False
        self.assign = False
        self.my_solutions = False
        self.all_solutions = False
        self.all_solutions_source_codes = False
        self.messages = False
        self.messages_all = False
        self.messages_send_any = False
        self.messages_send_own = False
        self.messages_delete_thread = False
        self.messages_resolve = False
        self.plagiarism = False
        self.quizzes = False
        self.quizzes_admin = False
        self.queue = False
        self.queue_admin = False

    def set_common(self):
        self.info = True
        self.problems = True
        self.standings = True
        self.sheet = True
        self.messages = True
        self.queue = True

    def set_student(self, own_solutions_access, all_solutions_access):
        self.set_common()

        self.submit = True
        self.my_problems = True
        self.my_solutions |= (own_solutions_access != SolutionAccessLevel.NO_ACCESS)
        self.all_solutions |= (all_solutions_access != SolutionAccessLevel.NO_ACCESS)
        self.messages_send_own = True
        self.quizzes = True

    def set_teacher(self):
        self.set_common()

        self.submit = True
        self.submit_all_problems = True
        self.editorials = True
        self.sheet_edit = True
        self.assign = True
        self.my_solutions = True
        self.all_solutions = True
        self.all_solutions_source_codes = False
        self.messages_all = True
        self.messages_send_any = True
        self.messages_delete_thread = True
        self.messages_resolve = True
        self.plagiarism = True
        self.quizzes_admin = True
        self.queue_admin = True

    def set_admin(self):
        self.set_common()

        self.sheet_edit = True
        self.assign = True
        self.settings = True
        self.all_solutions = True
        self.all_solutions_source_codes = True
        self.messages_all = True
        self.messages_send_any = True
        self.messages_delete_thread = True
        self.messages_resolve = True
        self.plagiarism = True
        self.quizzes_admin = True
        self.queue_admin = True

    def disable_sheet(self):
        self.sheet = False
        self.sheet_edit = False


InCourseAccessPermissions = namedtuple('InCourseAccessPermissions', 'course permissions')

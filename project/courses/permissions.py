from collections import namedtuple

from solutions.permissions import SolutionPermissions


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
        self.messages = False
        self.messages_all = False
        self.messages_send_any = False
        self.messages_send_own = False
        self.messages_delete_thread = False
        self.messages_resolve = False
        self.quizzes = False
        self.quizzes_admin = False
        self.queue = False
        self.queue_admin = False
        self.student_names = False

        self.my_solutions_permissions = SolutionPermissions()
        self.all_solutions_permissions = SolutionPermissions()

    @property
    def my_solutions(self):
        return self.my_solutions_permissions.can_view_state

    @property
    def all_solutions(self):
        return self.all_solutions_permissions.can_view_state

    def set_common(self):
        self.info = True
        self.problems = True
        self.standings = True
        self.sheet = True
        self.messages = True
        self.queue = True

    def set_student(self):
        self.set_common()

        self.submit = True
        self.my_problems = True
        self.messages_send_own = True
        self.quizzes = True

    def set_teacher(self):
        self.set_common()

        self.submit = True
        self.submit_all_problems = True
        self.editorials = True
        self.sheet_edit = True
        self.assign = True
        self.messages_all = True
        self.messages_send_any = True
        self.messages_delete_thread = True
        self.messages_resolve = True
        self.quizzes_admin = True
        self.queue_admin = True
        self.student_names = True

    def set_admin(self):
        self.set_common()

        self.sheet_edit = True
        self.assign = True
        self.settings = True
        self.messages_all = True
        self.messages_send_any = True
        self.messages_delete_thread = True
        self.messages_resolve = True
        self.quizzes_admin = True
        self.queue_admin = True
        self.student_names = True

    def disable_sheet(self):
        self.sheet = False
        self.sheet_edit = False


InCourseAccessPermissions = namedtuple('InCourseAccessPermissions', 'course permissions')

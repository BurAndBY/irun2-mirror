from collections import namedtuple

from solutions.permissions import SolutionAccessLevel

from .models import Membership, Course


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
        self.all_solutions_source_codes = False

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
        self.all_solutions_source_codes = False

    def set_admin(self):
        self.set_common()

        self.settings = True
        self.all_solutions = True
        self.all_solutions_source_codes = True

    def disable_sheet(self):
        self.sheet = False
        self.sheet_edit = False


InCourseAccessLevel = namedtuple('InCourseAccessLevel', 'course level')


def calculate_course_solution_access_level(solution, user):
    level = SolutionAccessLevel.NO_ACCESS

    course = Course.objects.\
        filter(coursesolution__solution_id=solution.id).\
        first()

    if course is None:
        # the solution does not belong to any course
        return InCourseAccessLevel(None, level)

    for role in Membership.objects.filter(course=course, user=user).values_list('role', flat=True):
        if role == Membership.STUDENT:
            if solution.author_id == user.id:
                level = max(level, course.student_own_solutions_access)
            else:
                level = max(level, course.student_all_solutions_access)
        elif role == Membership.TEACHER:
            level = max(level, SolutionAccessLevel.FULL)

    # level remains NO_ACCESS if user is not a member of the course

    return InCourseAccessLevel(course, level)

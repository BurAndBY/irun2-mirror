from users.modelfields import is_instance_owned
from solutions.permissions import SolutionAccessLevel, SolutionPermissions

from .models import Membership, Course, CourseStatus
from .permissions import CoursePermissions, InCourseAccessPermissions


class CourseMemberFlags(object):
    def __init__(self):
        # Both flags may be true
        self.is_student = False
        self.is_teacher = False

        # Staff member or a member of an admin group that owns the course
        self.is_admin = False

    @staticmethod
    def load(course, user):
        flags = CourseMemberFlags()

        for role in Membership.objects.filter(course=course, user=user).values_list('role', flat=True):
            if role == Membership.STUDENT:
                flags.is_student = True
            elif role == Membership.TEACHER:
                flags.is_teacher = True

        if is_instance_owned(course, user):
            flags.is_admin = True

        return flags


def calculate_course_permissions(course, member_flags):
    '''
    Memberships should refer the same user and the given course.
    '''
    permissions = CoursePermissions()

    if member_flags.is_student:
        permissions.set_student()
    if member_flags.is_teacher:
        permissions.set_teacher()
    if member_flags.is_admin:
        permissions.set_admin()

    permissions.my_solutions_permissions = _calculate_course_solution_permissions(course, member_flags, True)
    permissions.all_solutions_permissions = _calculate_course_solution_permissions(course, member_flags, False)

    if not course.enable_sheet:
        permissions.sheet = False

    if not course.enable_queues:
        permissions.queue = False
        permissions.queue_admin = False

    if course.status == CourseStatus.ARCHIVED:
        permissions.submit = False
        permissions.submit_all_problems = False

    if not course.private_mode:
        permissions.student_names = True

    return permissions


def _calculate_course_solution_level(course, member_flags, i_am_author):
    level = SolutionAccessLevel.NO_ACCESS
    if member_flags.is_student:
        if i_am_author:
            level = max(level, course.student_own_solutions_access)
        else:
            level = max(level, course.student_all_solutions_access)

    if member_flags.is_teacher:
        level = max(level, course.teacher_all_solutions_access)

    if member_flags.is_admin:
        level = max(level, SolutionAccessLevel.FULL)

    return level


def _calculate_course_solution_permissions(course, member_flags, i_am_author):
    level = _calculate_course_solution_level(course, member_flags, i_am_author)
    permissions = SolutionPermissions()
    permissions.update(level)

    if (course.status == CourseStatus.ARCHIVED) and (not member_flags.is_admin):
        # avoid cheating: students get into old student accounts and steal their solutions
        permissions.deny_view_source_code()

    if member_flags.is_teacher or member_flags.is_admin:
        permissions.allow_view_ip_address()
        permissions.allow_view_plagiarism_score()

    return permissions


def calculate_course_solution_permissions_ex(solution, user):
    course = Course.objects.filter(coursesolution__solution_id=solution.id).order_by().first()
    if course is None:
        # the solution does not belong to any course
        return InCourseAccessPermissions(None, SolutionPermissions())

    member_flags = CourseMemberFlags.load(course, user)
    permissions = _calculate_course_solution_permissions(course, member_flags, solution.author_id == user.id)
    return InCourseAccessPermissions(course, permissions)

from users.admingroups.utils import user_belongs_to_group
from solutions.permissions import SolutionAccessLevel

from .models import Membership, Course, CourseStatus
from .permissions import CoursePermissions, InCourseAccessLevel


def calculate_course_permissions(course, user, memberships):
    '''
    Memberships should refer the same user and the given course.
    '''
    permissions = CoursePermissions()

    for membership in memberships:
        assert membership.user_id == user.id
        assert membership.course_id == course.id

        if membership.role == Membership.STUDENT:
            permissions.set_student(course.student_own_solutions_access, course.student_all_solutions_access)
        elif membership.role == Membership.TEACHER:
            permissions.set_teacher()

    if user.is_staff:
        permissions.set_admin()
    elif user.is_admin and (course.owner_id is not None):
        if user_belongs_to_group(user, course.owner_id):
            permissions.set_admin()

    if not course.enable_sheet:
        permissions.sheet = False

    if not course.enable_queues:
        permissions.queue = False
        permissions.queue_admin = False

    if course.status == CourseStatus.ARCHIVED:
        permissions.submit = False
        permissions.submit_all_problems = False

    return permissions


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
            level = max(level, course.teacher_all_solutions_access)

    # level remains NO_ACCESS if user is not a member of the course

    if course.status == CourseStatus.ARCHIVED:
        level = min(level, SolutionAccessLevel.STATE)

    return InCourseAccessLevel(course, level)

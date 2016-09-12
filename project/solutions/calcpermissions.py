from contests.calcpermissions import calculate_contest_solution_access_level
from courses.calcpermissions import calculate_course_solution_access_level

from .permissions import SolutionAccessLevel, SolutionPermissions, SolutionEnvironment


def calculate_permissions(solution, user):
    level = SolutionAccessLevel.NO_ACCESS

    # course
    in_course = calculate_course_solution_access_level(solution, user)
    level = max(level, in_course.level)

    # contest
    in_contest = calculate_contest_solution_access_level(solution, user)
    level = max(level, in_contest.level)

    permissions = SolutionPermissions()
    permissions.update(level)

    if in_contest.contest is not None and in_contest.samples_only_state:
        permissions.state = False

    if user.is_staff:
        permissions.set_all()

    return (permissions, SolutionEnvironment(in_course.course, in_contest.contest))

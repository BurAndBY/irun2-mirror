from courses.calcpermissions import calculate_course_solution_access_level

from .permissions import SolutionAccessLevel, SolutionPermissions, SolutionEnvironment


def calculate_permissions(solution, user):
    level = SolutionAccessLevel.NO_ACCESS

    # course
    in_course = calculate_course_solution_access_level(solution, user)
    level = max(level, in_course.level)

    # contest
    # TODO when contests are ready

    permissions = SolutionPermissions()
    permissions.update(level)

    if user.is_staff:
        permissions.set_all()

    return (permissions, SolutionEnvironment(in_course.course))

from contests.calcpermissions import calculate_contest_solution_permissions_ex
from courses.calcpermissions import calculate_course_solution_permissions_ex
from problems.calcpermissions import calculate_problem_solution_permissions

from solutions.permissions import SolutionPermissions, SolutionEnvironment


def calculate_permissions(solution, user):
    permissions = SolutionPermissions()

    # course
    in_course = calculate_course_solution_permissions_ex(solution, user)
    permissions |= in_course.permissions

    # contest
    in_contest = calculate_contest_solution_permissions_ex(solution, user)
    permissions |= in_contest.permissions

    # problem
    permissions |= calculate_problem_solution_permissions(solution, user)

    if user.is_staff:
        permissions.allow_view_ip_address()

    return (permissions, SolutionEnvironment(in_course.course, in_course.link_to_course,
                                             in_contest.contest, in_contest.link_to_contest))

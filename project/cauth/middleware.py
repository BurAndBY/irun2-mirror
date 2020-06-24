import functools
from collections import namedtuple

from django.db import connection
from django.utils.functional import SimpleLazyObject

from users.models import AdminGroup
from problems.models import ProblemAccess
from quizzes.models import CategoryAccess

Flags = namedtuple('Flags', ['has_access_to_problems', 'has_access_to_quizzes', 'has_access_to_admin'])


class AdminMiddleware(object):
    '''
    Sets user flags:
      * user.is_admin
      * user.is_problem_editor

    Note that is_staff => is_admin => is_problem_editor
    '''
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None:
            request.user = SimpleLazyObject(functools.partial(self._verify_user, user))

        response = self.get_response(request)
        return response

    def _get_access(self, user):
        if user.is_authenticated:
            if user.is_staff:
                return Flags(True, True, True)

            with connection.cursor() as cursor:
                cursor.execute('SELECT '
                               '(SELECT 1 FROM {problems_problemaccess} WHERE user_id = %s) AS has_access_to_problems, '
                               '(SELECT 1 FROM {quizzes_categoryaccess} WHERE user_id = %s) AS has_access_to_quizzes, '
                               '(SELECT 1 FROM {users_admingroup_users} WHERE user_id = %s) AS has_access_to_admin'.format(
                                    problems_problemaccess=ProblemAccess._meta.db_table,
                                    quizzes_categoryaccess=CategoryAccess._meta.db_table,
                                    users_admingroup_users=AdminGroup.users.through._meta.db_table
                                ), [user.id, user.id, user.id])
                profile = cursor.fetchone()
                return Flags(*profile)

        return Flags(False, False, False)

    def _verify_user(self, user):
        access = self._get_access(user)
        user.is_admin = access.has_access_to_admin
        user.is_problem_editor = user.is_admin or access.has_access_to_problems
        user.is_quiz_editor = user.is_admin or access.has_access_to_quizzes
        return user

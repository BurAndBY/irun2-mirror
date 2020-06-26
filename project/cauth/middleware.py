import functools
from collections import namedtuple

from django.db import connection
from django.utils.functional import SimpleLazyObject

from users.models import AdminGroup
from problems.models import ProblemAccess
from quizzes.models import CategoryAccess

Flags = namedtuple('Flags', ['has_access_to_problems', 'has_access_to_quizzes'])


class AdminMiddleware(object):
    '''
    Sets user flags:
      * user.is_admin
      * user.is_problem_editor
      * user.is_quiz_editor

    Note that is_staff => is_admin => {is_problem_editor, is_quiz_editor}
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
        with connection.cursor() as cursor:
            cursor.execute('SELECT '
                           '(SELECT 1 FROM {problems_problemaccess} WHERE user_id = %s) AS has_access_to_problems, '
                           '(SELECT 1 FROM {quizzes_categoryaccess} WHERE user_id = %s) AS has_access_to_quizzes'.format(
                                problems_problemaccess=ProblemAccess._meta.db_table,
                                quizzes_categoryaccess=CategoryAccess._meta.db_table,
                            ), [user.id, user.id])
            profile = cursor.fetchone()
            return Flags(*profile)

    def _is_admin(self, user):
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True

        user.admingroup_ids = AdminGroup.users.through.objects.\
            filter(user_id=user.id).\
            values_list('admingroup_id', flat=True)
        if len(user.admingroup_ids) > 0:
            return True

        return False

    def _verify_user(self, user):
        if self._is_admin(user):
            user.is_admin = True
            user.is_problem_editor = True
            user.is_quiz_editor = True
        else:
            user.is_admin = False
            if user.is_authenticated:
                access = self._get_access(user)
                user.is_problem_editor = access.has_access_to_problems
                user.is_quiz_editor = access.has_access_to_quizzes
            else:
                user.is_problem_editor = False
                user.is_quiz_editor = False
        return user

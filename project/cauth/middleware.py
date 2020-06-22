import functools
from collections import namedtuple

from django.utils.functional import SimpleLazyObject

from users.models import UserProfile

Flags = namedtuple('Flags', ['has_access_to_problems', 'has_access_to_admin'])


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
                return Flags(True, True)

            try:
                profile = UserProfile.objects.filter(pk=user.id).values_list('has_access_to_problems', 'has_access_to_admin').get()
                return Flags(*profile)
            except UserProfile.DoesNotExist:
                pass

        return Flags(False, False)

    def _verify_user(self, user):
        access = self._get_access(user)
        user.is_admin = access.has_access_to_admin
        user.is_problem_editor = user.is_admin or access.has_access_to_problems
        return user

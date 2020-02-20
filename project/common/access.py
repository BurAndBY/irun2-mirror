import inspect

from django.core.exceptions import PermissionDenied
from django.http import Http404

FUNC_PREFIX = 'can_'


class Permissions(object):
    '''
    example:
    class MyPermissions(Permissions):
        FOO = 1 << 0
        BAR = 1 << 1
    '''

    def __init__(self, mask=0):
        Permissions._validate(mask)
        self._value = mask

    @classmethod
    def all(cls):
        mask = 0
        for _, value in cls.items():
            mask |= value
        return cls(mask)

    @classmethod
    def items(cls):
        for name, value in inspect.getmembers(cls):
            if not name.startswith('__') and not callable(value):
                yield name, value

    def set(self, mask):
        Permissions._validate(mask)
        self._value |= mask

    def __getattr__(self, name):
        if name.startswith(FUNC_PREFIX):
            name = name[len(FUNC_PREFIX):].upper()
            cls = type(self)
            ref_value = getattr(cls, name)
            cur_value = self._value
            return (cur_value & ref_value) == ref_value
        return super(Permissions, self).__getattr__(name)

    def check(self, mask):
        '''
        Returns true if all requirements are satisfied.
        '''
        Permissions._validate(mask)
        return (self._value & mask) == mask

    @staticmethod
    def _validate(mask):
        if not isinstance(mask, int):
            raise TypeError('the value must be int, not {}'.format(type(mask).__name__))


class PermissionCheckMixin(object):
    '''
    To use this mixin with your view, you should:
      * implement "_make_permissions" method,
      * (optionally) set "requirements" or "requirements_to_post" class field.
    '''
    requirements = 0
    requirements_to_post = None

    def _make_permissions(self, user):
        '''
        If the function returns None, access is denied.
        '''
        raise NotImplementedError

    def _check_permissions(self, permissions, request):
        if (self.requirements_to_post is not None) and (request.method == 'POST'):
            reqs_to_check = self.requirements_to_post
        else:
            reqs_to_check = self.requirements

        if not permissions.check(reqs_to_check):
            raise PermissionDenied

    def dispatch(self, request, *args, **kwargs):
        self.permissions = self._make_permissions(request.user)
        if self.permissions is None:
            raise Http404('Object does not exist or access is denied')
        self._check_permissions(self.permissions, request)
        return super(PermissionCheckMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PermissionCheckMixin, self).get_context_data(**kwargs)
        context['permissions'] = self.permissions
        return context

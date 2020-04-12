from itertools import chain

from django.core.exceptions import PermissionDenied
from django.http import Http404


class PermissionsType(type):
    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)
        items = []
        for key, value in dct.items():
            if name.startswith('__') or not isinstance(value, int):
                continue
            setattr(x, 'allow_{}'.format(key.lower()), classmethod(lambda cls, v=value: cls(v)))
            setattr(x, 'can_{}'.format(key.lower()), property(lambda self, v=value: self._value & v == v))
            items.append((key, value))

        x._ITEMS_ = tuple(chain(x._ITEMS_, items))
        return x


class Permissions(metaclass=PermissionsType):
    '''
    example:
    class MyPermissions(Permissions):
        FOO = 1 << 0
        BAR = 1 << 1
    '''
    _ITEMS_ = ()

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
    def basic(cls):
        return cls(0)

    @classmethod
    def items(cls):
        return cls._ITEMS_

    def set(self, mask):
        Permissions._validate(mask)
        self._value |= mask

    def check(self, mask):
        '''
        Returns true if all requirements are satisfied.
        '''
        Permissions._validate(mask)
        return (self._value & mask) == mask

    def __and__(self, other):
        if type(self) is not type(other):
            raise TypeError('permissions of different types cannot be combined')
        return type(self)(self._value | other._value)

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

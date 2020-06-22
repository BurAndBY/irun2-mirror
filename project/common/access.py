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

    To get an instance of MyPermissions class
    that contains a permission mask, you may use:
    * MyPermissions.basic() or MyPermissions.all();
    * MyPermissions.allow_foo(), ...;
    * an &-combination of permissions.
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

    def __or__(self, other):
        if type(self) is not type(other):
            raise TypeError('permissions of different types cannot be combined')
        return type(self)(self._value | other._value)

    def __le__(self, other):
        if type(self) is not type(other):
            raise TypeError('permissions of different types cannot be compared')
        return (self._value & other._value) == self._value


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

    def _make_permissions(self, request_user):
        '''
        If the function returns None, access is denied.
        '''
        raise NotImplementedError

    def _can_handle_request(self):
        return self.permissions.check(self.requirements)

    def _can_handle_post_request(self):
        if self.requirements_to_post is not None:
            return self.permissions.check(self.requirements_to_post)
        return self._can_handle_request()

    def dispatch(self, request, *args, **kwargs):
        self.permissions = self._make_permissions(request.user)
        if self.permissions is None:
            raise Http404('Object does not exist or access is denied')

        check = self._can_handle_post_request() if (request.method == 'POST') else self._can_handle_request()
        if not check:
            raise PermissionDenied

        return super(PermissionCheckMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PermissionCheckMixin, self).get_context_data(**kwargs)
        context['permissions'] = self.permissions
        return context


class PermissionMap(object):
    '''
    {pk -> Permissions}
    '''
    def __init__(self, pks):
        self._map = {pk: None for pk in pks}

    @staticmethod
    def _update(current_perms, new_perms):
        return new_perms if current_perms is None else (current_perms | new_perms)

    def grant(self, pk, new_perms):
        if pk not in self._map:
            return
        self._map[pk] = PermissionMap._update(self._map.get(pk), new_perms)

    def grant_all(self, new_perms):
        for pk, current_perms in self._map.items():
            self._map[pk] = PermissionMap._update(current_perms, new_perms)

    def find_pks_for_granting(self, possible_perms):
        pks = []
        for pk, current_perms in self._map.items():
            if (current_perms is None) or not (possible_perms <= current_perms):
                pks.append(pk)
        return pks

    def map(self):
        return self._map


class PermissionCalcer(object):
    permissions_cls = None

    def __init__(self, request_user):
        self.user = request_user

    def calc(self, object_id):
        pm = PermissionMap([object_id])
        self.fill_permission_map(pm)
        return pm.map().get(object_id)

    def calc_in_bulk(self, object_ids):
        pm = PermissionMap(object_ids)
        self.fill_permission_map(pm)
        return pm.map()

    def filter_objects(self, object_ids, requirement=0):
        object_ids = list(object_ids)
        permissions = self.calc_in_bulk(object_ids)
        result = []
        for object_id in object_ids:
            p = permissions.get(object_id)
            if (p is not None) and (p.check(requirement)):
                result.append(object_id)
        return result

    def fill_permission_map(self, pm):
        if not self.user.is_authenticated:
            return

        if self.user.is_staff:
            pm.grant_all(self.permissions_cls.all())
            return

        self._do_fill_permission_map(pm)

    def _do_fill_permission_map(self, pm):
        raise NotImplementedError()

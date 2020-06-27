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
            setattr(x, 'allow_{}'.format(key.lower()), lambda self, v=value: self._set_bits(v))
            setattr(x, 'deny_{}'.format(key.lower()), lambda self, v=value: self._unset_bits(v))
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
    * MyPermissions();
    * MyPermissions().allow_all();
    * MyPermissions().allow_foo().allow_bar(), ...;
    * an |-combination of permission masks.
    '''
    _ITEMS_ = ()

    def __init__(self, mask=0):
        Permissions._validate(mask)
        self._value = mask

    def clone(self):
        return type(self)(self._value)

    def _set_bits(self, value):
        self._value |= value
        return self

    def _unset_bits(self, value):
        self._value &= ~value
        return self

    def allow_all(self):
        for _, value in type(self).items():
            self._value |= value
        return self

    def deny_all(self):
        self._value = 0
        return self

    @classmethod
    def items(cls):
        return cls._ITEMS_

    def check(self, mask):
        '''
        Returns true if all requirements are satisfied.
        '''
        Permissions._validate(mask)
        return (self._value & mask) == mask

    def __ior__(self, other):
        if type(self) is not type(other):
            raise TypeError('permissions of different types cannot be combined')
        self._value |= other._value

    @property
    def mask(self):
        return self._value

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
        self._map = {}
        for pk in pks:
            if not isinstance(pk, int):
                raise TypeError('primary keys are expected to be integers')
            self._map[pk] = None

    def grant(self, pk, new_perms):
        try:
            current_perms = self._map[pk]
        except KeyError:
            return
        self._update(pk, current_perms, new_perms)

    def grant_all(self, new_perms):
        for pk, current_perms in self._map.items():
            self._update(pk, current_perms, new_perms)

    def find_pks_for_granting(self, possible_perms):
        pks = []
        for pk, current_perms in self._map.items():
            if (current_perms is None) or (not current_perms.check(possible_perms.mask)):
                pks.append(pk)
        return pks

    def map(self):
        return self._map

    def _update(self, pk, current_perms, new_perms):
        if current_perms is not None:
            current_perms |= new_perms
        else:
            self._map[pk] = new_perms.clone()


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
            pm.grant_all(self.permissions_cls().allow_all())
            return

        self._do_fill_permission_map(pm)

    def _do_fill_permission_map(self, pm):
        raise NotImplementedError()

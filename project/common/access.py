from django.core.exceptions import PermissionDenied

FUNC_PREFIX = 'can_'


class Permissions(object):
    '''
    example:
    class MyPermissions(Permissions):
        FOO = 1 << 0
        BAR = 1 << 1
    '''

    def __init__(self, mask=0):
        self._value = mask

    def set(self, mask):
        self._value |= mask

    def __getattr__(self, name):
        if name.startswith(FUNC_PREFIX):
            name = name[len(FUNC_PREFIX):].upper()
            cls = type(self)
            ref_value = getattr(cls, name)
            cur_value = self._value
            return (cur_value & ref_value) != 0
        return super(Permissions, self).__getattr__(name)

    def check(self, mask):
        '''
        Returns true if all requirements are satisfied.
        '''
        return (self._value & mask) == mask


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
            raise PermissionDenied
        self._check_permissions(self.permissions, request)
        return super(PermissionCheckMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PermissionCheckMixin, self).get_context_data(**kwargs)
        context['permissions'] = self.permissions
        return context

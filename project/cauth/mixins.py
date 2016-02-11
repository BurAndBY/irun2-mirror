from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator


class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


def _is_staff(user):
    if not user.is_staff:
        raise PermissionDenied
    return True


class StaffMemberRequiredMixin(object):
    @method_decorator(login_required)
    @method_decorator(user_passes_test(_is_staff))
    def dispatch(self, request, *args, **kwargs):
        return super(StaffMemberRequiredMixin, self).dispatch(request, *args, **kwargs)

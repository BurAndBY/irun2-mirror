from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import PermissionRequiredMixin
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


class ProblemEditorMemberRequiredMixin(PermissionRequiredMixin):
    def has_permission(self):
        return self.request.user.is_problem_editor


class UserPassesTestMixin(object):
    """
    Deny a request with a permission error if the test_func() method returns False.
    """

    def test_func(self):
        raise NotImplementedError(
            '{0} is missing the implementation of the test_func() method.'.format(self.__class__.__name__)
        )

    def dispatch(self, request, *args, **kwargs):
        user_test_result = self.test_func()
        if not user_test_result:
            raise PermissionDenied
        return super(UserPassesTestMixin, self).dispatch(request, *args, **kwargs)

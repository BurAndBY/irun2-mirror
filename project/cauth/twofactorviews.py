from django.conf import settings
from django.contrib import auth

import two_factor.forms as tfforms
import two_factor.views as tfviews

from cauth.forms import AuthenticationFormWithRememberMe, TOTPDeviceForm


def patch_form_list(forms, src_cls, dst_cls):
    return tuple((k, dst_cls if v is src_cls else v) for k, v in forms)


class LoginView(tfviews.LoginView):
    template_name = 'cauth/two_factor/core/login.html'
    form_list = patch_form_list(tfviews.LoginView.form_list, auth.forms.AuthenticationForm, AuthenticationFormWithRememberMe)

    def post(self, *args, **kwargs):
        # sobols@: This is a nasty hack to make "Remember me" checkbox.
        # Inspired by https://djangosnippets.org/snippets/1881/
        # TODO: Fix an issue described in comments there.
        if self.request.POST.get('auth-remember_me', None):
            self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        return super(LoginView, self).post(*args, **kwargs)


class ProfileView(tfviews.ProfileView):
    template_name = 'cauth/two_factor/profile/profile.html'


class DisableView(tfviews.DisableView):
    template_name = 'cauth/two_factor/profile/disable.html'


class SetupView(tfviews.SetupView):
    template_name = 'cauth/two_factor/core/setup.html'
    form_list = patch_form_list(tfviews.SetupView.form_list, tfforms.TOTPDeviceForm, TOTPDeviceForm)


class SetupCompleteView(tfviews.SetupCompleteView):
    template_name = 'cauth/two_factor/core/setup_complete.html'


class QRGeneratorView(tfviews.QRGeneratorView):
    pass


class BackupTokensView(tfviews.BackupTokensView):
    template_name = 'cauth/two_factor/core/backup_tokens.html'

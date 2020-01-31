import django.contrib.auth.views

import cauth.forms


class PasswordChangeView(django.contrib.auth.views.PasswordChangeView):
    extra_context = {'disable_change_password_warning': True}
    form_class = cauth.forms.PasswordChangeForm

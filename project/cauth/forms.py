from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _


class AuthenticationFormWithRememberMe(AuthenticationForm):
    remember_me = forms.BooleanField(label=_('Remember me'), required=False)

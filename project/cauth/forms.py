from django import forms
from django.contrib.auth.forms import AuthenticationForm


class AuthenticationFormWithRememberMe(AuthenticationForm):
    remember_me = forms.BooleanField(required=False)

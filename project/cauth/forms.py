from django import forms
from django.contrib import auth
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

import two_factor.forms

from users.models import UserProfile


class AuthenticationFormWithRememberMe(auth.forms.AuthenticationForm):
    remember_me = forms.BooleanField(label=_('Remember me'), required=False)


class PasswordChangeForm(auth.forms.PasswordChangeForm):
    def save(self, commit=True):
        with transaction.atomic():
            result = super(PasswordChangeForm, self).save(commit)
            profile = self.user.userprofile
            if profile is not None:
                profile.needs_change_password = False
                profile.save()

            return result


# for proper field ordering
PasswordChangeForm.base_fields = auth.forms.PasswordChangeForm.base_fields


class UserNameForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = ['last_name', 'first_name']


class UserProfileNameForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['patronymic']


class UserForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = ['email']


# 2FA: override field widget appearance
class TOTPDeviceForm(two_factor.forms.TOTPDeviceForm):
    token = forms.IntegerField(
        label=_('Token'), required=False,
        widget=forms.NumberInput(attrs={'autofocus': '1'})
    )

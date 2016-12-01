from django import forms
from django.contrib import auth
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

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


class UserForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = ['email', 'last_name', 'first_name']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['patronymic']

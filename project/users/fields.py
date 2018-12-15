from django import forms
from django.contrib import auth
from django.utils.translation import ugettext_lazy as _


class UsernameField(forms.CharField):
    widget = forms.TextInput(attrs={'placeholder': _('Username')})

    default_error_messages = {
        'does_not_exist': _('User %(username)s not found.'),
    }

    def to_python(self, value):
        value = super(UsernameField, self).to_python(value)

        user_model = auth.get_user_model()
        user_id = user_model.objects.filter(username=value).values_list('id', flat=True).first()
        if user_id is None:
            raise forms.ValidationError(self.error_messages['does_not_exist'], params={'username': value})

        return user_id

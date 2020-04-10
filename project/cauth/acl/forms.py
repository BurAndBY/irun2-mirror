from django import forms
from django.utils.translation import ugettext_lazy as _

from .accessmode import AccessMode
from users.fields import UsernameField


class ShareWithUserForm(forms.Form):
    user = UsernameField(label=_('Username'), required=True)
    mode = forms.ChoiceField(label=_('Access mode'), required=True, choices=AccessMode.CHOICES, initial=AccessMode.WRITE)

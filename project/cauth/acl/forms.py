from django import forms
from django.utils.translation import ugettext_lazy as _

from common.constants import EMPTY_SELECT
from users.fields import UsernameField
from users.models import AdminGroup

from .accessmode import AccessMode


class ShareWithUserForm(forms.Form):
    user = UsernameField(label=_('Username'), required=True)
    mode = forms.ChoiceField(label=_('Access mode'), required=True, choices=AccessMode.CHOICES, initial=AccessMode.MODIFY)


class ShareWithGroupForm(forms.Form):
    group = forms.ModelChoiceField(label=_('Group'), queryset=AdminGroup.objects.all(), required=True, empty_label=EMPTY_SELECT)
    mode = forms.ChoiceField(label=_('Access mode'), required=True, choices=AccessMode.CHOICES, initial=AccessMode.MODIFY)

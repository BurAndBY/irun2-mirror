from django import forms
from django.utils.translation import ugettext_lazy as _

from common.accessmode import AccessMode
from users.fields import UsernameField

from .models import GroupQuizRelation


class AddQuestionGroupForm(forms.ModelForm):
    class Meta:
        model = GroupQuizRelation
        fields = ['group', 'points']


class UploadFileForm(forms.Form):
    file = forms.FileField(label=_('File'))


class ShareCategoryForm(forms.Form):
    user = UsernameField(label=_('Username'), required=True)
    mode = forms.ChoiceField(label=_('Access mode'), required=True, choices=AccessMode.CHOICES, initial=AccessMode.WRITE)

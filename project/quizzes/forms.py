from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import GroupQuizRelation


class AddQuestionGroupForm(forms.ModelForm):
    class Meta:
        model = GroupQuizRelation
        fields = ['group', 'points']


class UploadFileForm(forms.Form):
    file = forms.FileField(label=_('File'))

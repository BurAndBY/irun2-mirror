from django import forms

from .models import GroupQuizRelation


class AddQuestionGroupForm(forms.ModelForm):
    class Meta:
        model = GroupQuizRelation
        fields = ['group', 'points']


class UploadFileForm(forms.Form):
    file = forms.FileField()

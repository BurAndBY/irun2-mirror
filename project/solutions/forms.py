from django import forms

from proglangs.models import ProgrammingLanguage


class AdHocForm(forms.Form):
    source_code = forms.CharField(widget=forms.Textarea)
    input_data = forms.CharField(widget=forms.Textarea)
    programming_language = forms.ModelChoiceField(queryset=ProgrammingLanguage.objects.all())

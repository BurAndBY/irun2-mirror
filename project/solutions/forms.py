from django import forms

from proglangs.models import Compiler


class AdHocForm(forms.Form):
    source_code = forms.CharField(widget=forms.Textarea)
    input_data = forms.CharField(widget=forms.Textarea)
    compiler = forms.ModelChoiceField(queryset=Compiler.objects.all().order_by('description'))

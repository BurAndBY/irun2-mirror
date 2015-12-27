from django import forms
from django.utils.translation import ugettext_lazy as _

from proglangs.models import Compiler


class AdHocForm(forms.Form):
    source_code = forms.CharField(widget=forms.Textarea)
    input_data = forms.CharField(widget=forms.Textarea)
    compiler = forms.ModelChoiceField(queryset=Compiler.objects.all().order_by('description'))


class SolutionForm(forms.Form):
    compiler = forms.ModelChoiceField(
        label=_('Compiler'),
        queryset=Compiler.objects.all().order_by('description')
    )
    text = forms.CharField(
        label=_('Enter source code'),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control'}),
        max_length=2**20
    )
    upload = forms.FileField(
        label=_('... or upload a file'),
        required=False,
        widget=forms.FileInput,
        max_length=255,
        help_text=_('If you select a file, text field content is ignored.')
    )

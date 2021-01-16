from __future__ import unicode_literals

from django import forms

from problems.models import ProblemRelatedFile


class ProblemSearchForm(forms.Form):
    query = forms.CharField(required=False)


TYPE_CHOICES = [(t, s) for t, s in ProblemRelatedFile.FILE_TYPE_CHOICES if t in ProblemRelatedFile.TEX_FILE_TYPES]


class TeXTechForm(forms.Form):
    source = forms.CharField(required=False, max_length=32768)
    renderer = forms.CharField(required=False, max_length=16)


class TeXRelatedFileForm(forms.Form):
    source = forms.CharField(required=False, max_length=32768, widget=forms.Textarea(attrs={'class': 'ir-monospace', 'rows': 20, 'autofocus': 'autofocus'}))
    file_type = forms.ChoiceField(required=True, choices=TYPE_CHOICES, initial=ProblemRelatedFile.STATEMENT_TEX_PYLIGHTEX)

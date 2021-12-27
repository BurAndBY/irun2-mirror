from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from common.locales.fields import CHOICES
from common.constants import EMPTY_SELECT
from proglangs.models import Compiler

from problems.models import Problem, ProblemFolder


class SimpleProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ['number', 'subnumber', 'full_name', 'short_name']


class ProblemFolderForm(forms.ModelForm):
    class Meta:
        model = ProblemFolder
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'autofocus': 'autofocus'}),
        }


class PolygonImportForm(forms.Form):
    upload = forms.FileField(label=_('Full package (Windows) as a ZIP-archive'), required=True, widget=forms.FileInput)
    language = forms.MultipleChoiceField(label=_('Problem statement language'), required=False, choices=CHOICES, widget=forms.CheckboxSelectMultiple)
    compiler = forms.ModelChoiceField(label=_('Compiler for checker and validator'), queryset=None, required=True, empty_label=EMPTY_SELECT)

    def __init__(self, *args, **kwargs):
        super(PolygonImportForm, self).__init__(*args, **kwargs)
        self.fields['compiler'].queryset = Compiler.objects.filter(language='cpp', default_for_courses=True)

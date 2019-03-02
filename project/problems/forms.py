from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from common.constants import EMPTY_SELECT
from proglangs.models import Compiler

from problems.models import Problem, ProblemFolder


class SimpleProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ['number', 'subnumber', 'full_name', 'short_name']


class ProblemSearchForm(forms.Form):
    query = forms.CharField(required=False)


class TeXForm(forms.Form):
    source = forms.CharField(required=False, max_length=32768, widget=forms.Textarea(attrs={'class': 'ir-monospace', 'rows': 20, 'autofocus': 'autofocus'}))
    renderer = forms.CharField(required=False, max_length=16)


class ProblemFolderForm(forms.ModelForm):
    class Meta:
        model = ProblemFolder
        fields = ['name']


class PolygonImportForm(forms.Form):
    LANGUAGE_CHOICES = (
        ('russian', _('Russian')),
        ('english', _('English')),
    )

    upload = forms.FileField(label=_('Full package (Windows) as a ZIP-archive'), required=True, widget=forms.FileInput)
    language = forms.ChoiceField(label=_('Problem statement language'), required=True, choices=LANGUAGE_CHOICES)
    compiler = forms.ModelChoiceField(label=_('Compiler for checker and validator'), queryset=None, required=True, empty_label=EMPTY_SELECT)

    def __init__(self, *args, **kwargs):
        super(PolygonImportForm, self).__init__(*args, **kwargs)
        self.fields['compiler'].queryset = Compiler.objects.filter(language='cpp', default_for_courses=True)

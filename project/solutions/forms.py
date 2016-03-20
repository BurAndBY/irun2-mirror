# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import ugettext_lazy as _

from common.constants import EMPTY_SELECT, make_empty_select
from proglangs.models import Compiler


class AdHocForm(forms.Form):
    source_code = forms.CharField(widget=forms.Textarea)
    input_data = forms.CharField(widget=forms.Textarea)
    compiler = forms.ModelChoiceField(queryset=Compiler.objects.all().order_by('description'))


class SolutionForm(forms.Form):
    compiler = forms.ModelChoiceField(
        label=_('Compiler'),
        queryset=Compiler.objects.all().order_by('description'),
        empty_label=EMPTY_SELECT,
    )
    text = forms.CharField(
        label=_('Enter source code'),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control ir-monospace'}),
        max_length=2**20
    )
    upload = forms.FileField(
        label=_(u'…or upload a file'),
        required=False,
        widget=forms.FileInput,
        max_length=255,
        help_text=_('If you select a file, text field content is ignored.')
    )

    def clean(self):
        cleaned_data = super(SolutionForm, self).clean()
        text = cleaned_data.get('text')
        upload = cleaned_data.get('upload')
        if (upload is None) and (text is not None) and (len(text) == 0):
            raise forms.ValidationError(_('Unable to submit an empty solution.'), code='empty')


class AllSolutionsFilterForm(forms.Form):
    STATE_CHOICES = (
        ('', make_empty_select(_('status'))),
        (_('state'), (
            ('waiting', _('Waiting')),
            ('preparing', _('Preparing')),
            ('compiling', _('Compiling')),
            ('testing', _('Testing')),
            ('finishing', _('Finishing')),
            ('done', _('Done')),
            ('not-done', _('Not Done')),
        )),
        (_('outcome'), (
            ('ok', _('Accepted')),
            ('ce', _('Compilation Error')),
            ('wa', _('Wrong Answer')),
            ('tle', _('Time Limit Exceeded')),
            ('mle', _('Memory Limit Exceeded')),
            ('ile', _('Idleness Limit Exceeded')),
            ('rte', _('Run-time Error')),
            ('pe', _('Presentation Error')),
            ('sv', _('Security Violation')),
            ('cf', _('Check Failed'))
        )),
    )
    state = forms.ChoiceField(choices=STATE_CHOICES, required=False)

    DEFAULT_COMPILER_CHOICES = (
        ('', make_empty_select(_('language'))),
        (_('language'), Compiler.LANGUAGE_CHOICES[1:]),
    )
    compiler = forms.ChoiceField(choices=DEFAULT_COMPILER_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        super(AllSolutionsFilterForm, self).__init__(*args, **kwargs)

        present_compiler_choices = ((_('compiler'), tuple(
            (unicode(compiler.id), unicode(compiler))
            for compiler in Compiler.objects.all()
        )), )

        self.fields['compiler'].choices = self.DEFAULT_COMPILER_CHOICES + present_compiler_choices


class CompareSolutionsForm(forms.Form):
    first = forms.IntegerField(min_value=0, label=_('First solution'), required=True)
    second = forms.IntegerField(min_value=0, label=_('Second solution'), required=True)
    diff = forms.BooleanField(label=_('Show only contextual differences, else show full files'), required=False)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from common.constants import EMPTY_SELECT, make_empty_select
from proglangs.models import Compiler
from proglangs.utils import guess_filename
from storage.validators import validate_filename


class AdHocForm(forms.Form):
    source_code = forms.CharField(widget=forms.Textarea)
    input_data = forms.CharField(widget=forms.Textarea)
    compiler = forms.ModelChoiceField(queryset=Compiler.objects.all().order_by('description'))


class SolutionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.file_size_limit = kwargs.pop('file_size_limit', None)
        super(SolutionForm, self).__init__(*args, **kwargs)

    compiler = forms.ModelChoiceField(
        label=_('Compiler'),
        required=True,
        queryset=Compiler.objects.all().order_by('description'),
        empty_label=EMPTY_SELECT,
    )
    text = forms.CharField(
        label=_('Enter source code'),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control ir-monospace', 'rows': 8}),
        max_length=2**20
    )
    upload = forms.FileField(
        label=_(u'…or upload a file'),
        required=False,
        widget=forms.FileInput,
        max_length=255,
        help_text=_('If you select a file, text field content is ignored.')
    )

    def _check_size(self, text, upload):
        if self.file_size_limit is None:
            return

        size = 0
        if upload is not None:
            size = upload.size
        elif text is not None:
            size = len(text.encode('utf-8'))

        if size > self.file_size_limit:
            raise forms.ValidationError(
                _('The size of the source file (%(actual)d B) exceeds the limit (%(limit)d B).'),
                code='too_big',
                params={'actual': size, 'limit': self.file_size_limit},
            )

    def clean(self):
        cleaned_data = super(SolutionForm, self).clean()
        text = cleaned_data.get('text')
        upload = cleaned_data.get('upload')
        compiler = cleaned_data.get('compiler')

        if (upload is None) and (text is not None) and (len(text) == 0):
            raise forms.ValidationError(_('Unable to submit an empty solution.'), code='empty')

        filename = None
        if upload is not None:
            filename = upload.name
        else:
            # need to guess filename
            if compiler is not None and text is not None:
                filename = guess_filename(compiler.language, text)

        if filename is None:
            raise forms.ValidationError(_('Unable to determine the name of the source file. '
                                          'For Java code, make sure you have a single public class defined. '
                                          'You can also try to upload a file instead of using direct input of code.'), code='no_name')

        validate_filename(filename)
        cleaned_data['filename'] = filename

        self._check_size(text, upload)
        return cleaned_data


class AllSolutionsFilterForm(forms.Form):
    STATE_CHOICES = (
        ('', make_empty_select(_('Status'))),
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
        (_('state'), (
            ('waiting', _('Waiting')),
            ('preparing', _('Preparing')),
            ('compiling', _('Compiling')),
            ('testing', _('Testing')),
            ('finishing', _('Finishing')),
            ('done', _('Done')),
            ('not-done', _('Not Done')),
        )),
    )
    state = forms.ChoiceField(choices=STATE_CHOICES, required=False)

    DEFAULT_COMPILER_CHOICES = (
        ('', make_empty_select(_('Language'))),
        (_('language'), Compiler.LANGUAGE_CHOICES[1:]),
    )
    compiler = forms.ChoiceField(choices=DEFAULT_COMPILER_CHOICES, required=False)

    problem = forms.IntegerField(label=_('Problem ID'), required=False, widget=forms.TextInput)
    user = forms.IntegerField(label=_('User ID'), required=False, widget=forms.TextInput)

    DIFFICULTY_CHOICES = (
        ('', make_empty_select(_('Level'))),
        ('no', _('No')),
        ('1-10', '1–10'),
        ('4', '4'),
        ('5-6', '5–6'),
        ('7-8', '7–8'),
        ('9-10', '9–10'),
    )
    difficulty = forms.ChoiceField(choices=DIFFICULTY_CHOICES, required=False)

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

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text

from common.constants import make_empty_select
from proglangs.models import Compiler
from proglangs.langlist import ProgrammingLanguage


class StateFilterForm(forms.Form):
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


class AllSolutionsFilterForm(StateFilterForm):
    DEFAULT_COMPILER_CHOICES = (
        ('', make_empty_select(_('Language'))),
        (_('language'), ProgrammingLanguage.CHOICES[1:]),
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
            (force_text(compiler.id), force_text(compiler))
            for compiler in Compiler.objects.all()
        )), )

        self.fields['compiler'].choices = self.DEFAULT_COMPILER_CHOICES + present_compiler_choices

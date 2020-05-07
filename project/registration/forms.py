# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import six

from django import forms
from django.core.exceptions import ValidationError
from django.utils.functional import lazy
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import smart_text

from common.constants import EMPTY_SELECT
from common.education.year import make_year_of_study_choices

from .models import (
    IcpcCoach,
    IcpcTeam,
    IcpcContestant,
)

FAKE_MESSAGES = [
    _('Ex.'),
    _('Format'),
]


def _format_example(key, value):
    return '{}: {}'.format(smart_text(gettext(key)), value)


def _ex(value):
    return lazy(_format_example, six.text_type)('Ex.', value)


def _fmt(value):
    return lazy(_format_example, six.text_type)('Format', value)


def _current_year():
    return datetime.date.today().year


def _year_choices(lower_bound, upper_bound):
    cur = _current_year()
    return [(None, EMPTY_SELECT)] + [(r, r) for r in range(cur + lower_bound, cur + upper_bound + 1)]


class BaseCoachForm(forms.ModelForm):
    class Meta:
        model = IcpcCoach
        fields = []
        help_texts = {
            'email': _ex('coach@example.com'),
            'first_name': _ex('Ivan'),
            'last_name': _ex('Ivanov'),
            'university': _ex('Bytelandian State University'),
            'faculty': _ex('Faculty of Information Technologies'),
        }


class CheckEmailMixin(object):
    def clean(self):
        cleaned_data = super().clean()
        if IcpcCoach.objects.filter(email=cleaned_data['email'], event=self.instance.event).exists():
            msg = _('This email has already been registered for this event.')
            self.add_error('email', msg)
        return cleaned_data


class IcpcCoachForm(CheckEmailMixin, BaseCoachForm):
    class Meta(BaseCoachForm.Meta):
        fields = ['email', 'first_name', 'last_name', 'university']


class IcpcCoachAsContestantForm(CheckEmailMixin, BaseCoachForm):
    year_of_study = forms.TypedChoiceField(label=_('Year of study'), required=False,
                                           choices=make_year_of_study_choices, coerce=int, empty_value=None)

    class Meta(BaseCoachForm.Meta):
        fields = ['email', 'first_name', 'last_name', 'university', 'faculty', 'year_of_study', 'group']


class IcpcCoachUpdateForm(BaseCoachForm):
    class Meta(BaseCoachForm.Meta):
        fields = ['first_name', 'last_name', 'university']


class IcpcCoachAsContestantUpdateForm(BaseCoachForm):
    year_of_study = forms.TypedChoiceField(label=_('Year of study'), required=False,
                                           choices=make_year_of_study_choices, coerce=int, empty_value=None)

    class Meta(BaseCoachForm.Meta):
        fields = ['first_name', 'last_name', 'university', 'faculty', 'year_of_study', 'group']


class IcpcTeamForm(forms.ModelForm):
    class Meta:
        model = IcpcTeam
        fields = ['name', 'participation_venue', 'participation_type']
        help_texts = {
            'name': _ex('Bytelandian SU #1: Dream Team')
        }


class IcpcContestantForm(forms.ModelForm):
    program_start_year = forms.TypedChoiceField(label=_('Program start year'), coerce=int, choices=_year_choices(-6, +1))
    graduation_year = forms.TypedChoiceField(label=_('Graduation year'), coerce=int, choices=_year_choices(-1, +6))
    date_of_birth = forms.DateField(
        label=_('Date of birth'),
        widget=forms.DateInput(format='%Y-%m-%d'),
        input_formats=['%Y-%m-%d'],
        help_text=_fmt('YYYY-MM-DD'),
    )

    class Meta:
        model = IcpcContestant
        fields = ['email', 'first_name', 'last_name', 'date_of_birth',
                  'study_program', 'program_start_year', 'graduation_year', 'sex']

        help_texts = {
            'email': _ex('student@example.com'),
            'first_name': _ex('Ivan'),
            'last_name': _ex('Ivanov'),
        }

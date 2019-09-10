# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import six

from django import forms
from django.utils.functional import lazy
from django.utils.text import format_lazy
from django.utils.translation import gettext
from django.utils.encoding import smart_text

from common.constants import EMPTY_SELECT

from .models import (
    IcpcCoach,
    IcpcTeam,
    IcpcContestant,
)


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


class IcpcCoachForm(forms.ModelForm):
    class Meta:
        model = IcpcCoach
        fields = ['email', 'first_name', 'last_name', 'university']
        help_texts = {
            'email': _ex('coach@example.com'),
            'first_name': _ex('Ivan'),
            'last_name': _ex('Ivanov'),
            'university': _ex('Bytelandian State University'),
        }


class IcpcTeamForm(forms.ModelForm):
    class Meta:
        model = IcpcTeam
        fields = ['name', 'participation_venue', 'participation_type']
        help_texts = {
            'name': _ex('Bytelandian SU #1: Dream Team')
        }


class IcpcContestantForm(forms.ModelForm):
    program_start_year = forms.TypedChoiceField(coerce=int, choices=_year_choices(-6, +1))
    graduation_year = forms.TypedChoiceField(coerce=int, choices=_year_choices(-1, +6))
    date_of_birth = forms.DateField(
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

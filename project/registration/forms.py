# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django import forms
from django.utils.translation import gettext_lazy as _

from common.constants import EMPTY_SELECT

from .models import (
    IcpcCoach,
    IcpcTeam,
    IcpcContestant,
)
from .example import Example, LocalizeMixin, _fmt


def _current_year():
    return datetime.date.today().year


def _year_choices(lower_bound, upper_bound):
    cur = _current_year()
    return [(None, EMPTY_SELECT)] + [(r, r) for r in range(cur + lower_bound, cur + upper_bound + 1)]


def _year_of_study_choices():
    return [('', '')] + [
        (year, '{}'.format(year))
        for year in range(1, 12)
    ]


def fix_help_texts(help_texts, **kwargs):
    new_help_texts = help_texts.copy()
    new_help_texts.update(kwargs)
    return new_help_texts


class BaseCoachForm(LocalizeMixin, forms.ModelForm):
    required_css_class = 'ir-required'

    class Meta:
        model = IcpcCoach
        fields = []
        help_texts = {
            'email': Example('coach@example.com'),
            'first_name': Example('Ivan', 'Иван'),
            'last_name': Example('Ivanov', 'Иванов'),
            'university': Example('Bytelandian State University', 'Байтландский государственный университет'),
            'faculty': Example('Faculty of Information Technologies', 'Факультет информационных технологий'),
            'postal_address': Example('220030, Minsk, 4 Nezavisimosti Ave.', '220030, г. Минск, пр. Независимости, д. 4'),
            'phone_number': Example('+375291234567', '+375291234567'),
        }
        widgets = {
            'university': forms.TextInput(attrs={'list': 'universities'}),
            'faculty': forms.TextInput(attrs={'list': 'faculties'}),
        }


class CheckEmailMixin(object):
    def clean(self):
        cleaned_data = super().clean()
        cur_email = cleaned_data.get('email')
        if cur_email is not None and IcpcCoach.objects.filter(email=cur_email, event=self.instance.event).exists():
            msg = _('This email has already been registered for this event.')
            self.add_error('email', msg)
        return cleaned_data


class IcpcCoachForm(CheckEmailMixin, BaseCoachForm):
    class Meta(BaseCoachForm.Meta):
        fields = ['email', 'first_name', 'last_name', 'university']


class IcpcCoachAsContestantForm(CheckEmailMixin, BaseCoachForm):
    year_of_study = forms.TypedChoiceField(label=_('Year of study'), required=False,
                                           choices=_year_of_study_choices, coerce=int, empty_value=None)

    class Meta(BaseCoachForm.Meta):
        fields = ['email', 'first_name', 'last_name', 'university', 'faculty', 'year_of_study']
        labels = {
            'university': _('Institution (university, school)'),
            'faculty': _('Faculty (if any)'),
        }


class IcpcCoachAsSchoolContestantForm(CheckEmailMixin, BaseCoachForm):
    year_of_study = forms.TypedChoiceField(label=_('Form'), required=False,
                                           choices=_year_of_study_choices, coerce=int, empty_value=None)

    class Meta(BaseCoachForm.Meta):
        fields = ['email', 'first_name', 'last_name', 'university', 'year_of_study', 'postal_address', 'phone_number']
        labels = {
            'university': _('School'),
        }
        help_texts = fix_help_texts(
            BaseCoachForm.Meta.help_texts,
            university=Example('Minsk School #1', 'СШ №1 г. Минска')
        )


class IcpcCoachUpdateForm(IcpcCoachForm):
    class Meta(IcpcCoachForm.Meta):
        fields = IcpcCoachForm.Meta.fields[1:]


class IcpcCoachAsContestantUpdateForm(IcpcCoachAsContestantForm):
    class Meta(IcpcCoachAsContestantForm.Meta):
        fields = IcpcCoachAsContestantForm.Meta.fields[1:]


class IcpcCoachAsSchoolContestantUpdateForm(IcpcCoachAsSchoolContestantForm):
    class Meta(IcpcCoachAsSchoolContestantForm.Meta):
        fields = IcpcCoachAsSchoolContestantForm.Meta.fields[1:]


class IcpcTeamForm(LocalizeMixin, forms.ModelForm):
    class Meta:
        model = IcpcTeam
        fields = ['name', 'participation_venue', 'participation_type']
        help_texts = {
            'name': Example('Bytelandian SU #1: Dream Team')
        }


class IcpcContestantForm(LocalizeMixin, forms.ModelForm):
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
            'email': Example('student@example.com'),
            'first_name': Example('Ivan', 'Иван'),
            'last_name': Example('Ivanov', 'Иванов'),
        }

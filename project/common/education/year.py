# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext as _
from django.utils import timezone


def make_year_of_study_string(year):
    return _('%(year)d year') % {'year': year}


def make_academic_year_string(year):
    return '{}–{}'.format(year, year + 1)


def make_year_of_study_choices():
    return [('', '')] + [
        (year, make_year_of_study_string(year))
        for year in range(1, 7)
    ]


def make_academic_year_choices():
    cur_year = timezone.now().date().year

    return [('', '')] + [
        (year, make_academic_year_string(year))
        for year in range(2004, cur_year + 2)
    ]

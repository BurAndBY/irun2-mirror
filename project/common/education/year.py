# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib.humanize.templatetags.humanize import ordinal
from django.utils.translation import ugettext as _
from django.utils.translation import get_language
from django.utils import timezone


def make_year_of_study_string(year):
    if get_language() == 'en':
        return '{} year'.format(ordinal(year))
    return _('%(year)d year') % {'year': year}


def make_group_string(group):
    return _('group #%(group)d') % {'group': group}


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

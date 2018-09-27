# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext as _


def make_year_of_study_string(year):
    return _('%(year)d year') % {'year': year}


def make_academic_year_string(year):
    return '{}–{}'.format(year, year + 1)

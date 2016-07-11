# -*- coding: utf-8 -*-

from django.utils.translation import ugettext as _


def make_year_of_study_string(year):
    return _(u'%(year)d year') % {'year': year}


def make_academic_year_string(year):
    return u'{}–{}'.format(year, year + 1)

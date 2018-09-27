# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat


EMPTY_SELECT = '—'
TREE_LEVEL_INDICATOR = '—'

STDIN = _('standard input')
STDOUT = _('standard output')
NO = _('no')
CHANGES_HAVE_BEEN_SAVED = _('Your changes have been saved.')
ACCEPTED_FOR_TESTING = _('Accepted for testing')


def make_empty_select(name):
    return string_concat('— ', name, ' —')

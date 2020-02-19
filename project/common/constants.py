# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _


EMPTY_SELECT = '—'

STDIN = _('standard input')
STDOUT = _('standard output')
NO = _('no')
CHANGES_HAVE_BEEN_SAVED = _('Your changes have been saved.')
ACCEPTED_FOR_TESTING = _('Accepted for testing')


def make_empty_select(name):
    return format_lazy('— {} —', name)

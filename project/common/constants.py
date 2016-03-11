# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat


EMPTY_SELECT = u'—'
TREE_LEVEL_INDICATOR = u'—'

STDIN = _('standard input')
STDOUT = _('standard output')
NO = _('no')


def make_empty_select(name):
    return string_concat(u'— ', name, u' —')

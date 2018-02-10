# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re

from . import photos


def extract_group(folder_name):
    m = re.search(r'\b(?P<group>\d+)\s+группа', folder_name)
    print m
    if m is not None:
        return m.group('group')

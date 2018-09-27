# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re


def extract_group(folder_name):
    m = re.search(r'\b(?P<group>\d+)\s+группа', folder_name)
    if m is not None:
        return m.group('group')

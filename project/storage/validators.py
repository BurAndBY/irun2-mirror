# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
import six

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

FORBIDDEN_CHARACTERS = r'"*:<>?\/|'
RESERVED_NAMES = re.compile(r'^(con|prn|aux|nul|com[1-9]|lpt[1-9])(\.|$)', re.IGNORECASE)


def validate_filename(value):
    if not isinstance(value, six.string_types):
        raise ValidationError(_('Filename must be a string'))

    if len(value) == 0:
        raise ValidationError(_('Filename cannot be empty'))

    for c in value:
        if (0 <= ord(c)) and (ord(c) <= 31):
            raise ValidationError(_('The use of characters in range 0–31 in filenames is forbidden'))

        if c in FORBIDDEN_CHARACTERS:
            raise ValidationError(
                _('Characters %(forbidden)s are reserved and cannot be used in filenames'),
                params={'forbidden': FORBIDDEN_CHARACTERS},
            )

    if RESERVED_NAMES.match(value):
        raise ValidationError(
            _('For compatibility with Windows, words CON, PRN, AUX, NUL, COM1…9, LPT1…9 are reserved and cannot be used as filenames')
        )

    if value.endswith(' ') or value.endswith('.'):
        raise ValidationError(_('Filename must not end with a space or a period'))

from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from proglangs.langlist import (
    list_language_codes,
    split_language_codes
)


class ProgrammingLanguagesField(forms.CharField):
    def __init__(self, **kwargs):
        kwargs['help_text'] = '{}: {}'.format(_('Possible choices'), ', '.join(list_language_codes()))
        super(ProgrammingLanguagesField, self).__init__(**kwargs)

    def clean(self, value):
        result = super(ProgrammingLanguagesField, self).clean(value)
        all_codes = set(list_language_codes())
        present_codes = []
        for code in split_language_codes(result):
            if code not in all_codes:
                raise ValidationError(_('Unknown programming language code: %(code)s'),
                                      params={'code': code}, code='unknown')
            if code not in present_codes:
                present_codes.append(code)

        return ', '.join(present_codes)

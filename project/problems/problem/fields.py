from __future__ import unicode_literals

import six

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError


class FloatStoredAsIntField(forms.FloatField):
    int_to_float_ratio = 1
    max_float_value = None

    def __init__(self, *args, **kwargs):
        kwargs['min_value'] = 0
        kwargs['help_text'] = self.help_text
        super(FloatStoredAsIntField, self).__init__(*args, **kwargs)

    def prepare_value(self, value):
        value = super(FloatStoredAsIntField, self).prepare_value(value)
        if isinstance(value, six.integer_types):
            if value == 0:
                return ''
            if value % self.int_to_float_ratio == 0:
                return value // self.int_to_float_ratio
            else:
                return float(value) / self.int_to_float_ratio

        return value

    def to_python(self, value):
        value = super(FloatStoredAsIntField, self).to_python(value)
        if value is None:
            return 0

        assert isinstance(value, float)

        if value < 0.:
            raise ValidationError(self.error_messages['negative'], code='negative')
        if self.max_float_value is not None and value > self.max_float_value:
            raise ValidationError(self.error_messages['too_big'], params={'limit': self.max_float_value}, code='too_big')

        intvalue = round(value * self.int_to_float_ratio)

        if intvalue == 0 and value > 0.:
            raise ValidationError(self.error_messages['too_small'], code='too_small')

        if intvalue == 0 and self.required:
            raise ValidationError(self.error_messages['required'], code='required')

        return intvalue


class TimeLimitField(FloatStoredAsIntField):
    default_error_messages = {
        'negative': _('Time limit cannot be negative.'),
        'too_big': _('Time limit is too big (exceeds %(limit)s s).'),
        'too_small': _('Time limit is too small.'),
    }
    help_text = _('Time limit per test measured in seconds (i. e. 0.5 or 2).')
    int_to_float_ratio = 1000
    max_float_value = 3600


class MemoryLimitField(FloatStoredAsIntField):
    default_error_messages = {
        'negative': _('Memory limit cannot be negative.'),
        'too_big': _('Memory limit is too big (exceeds %(limit)s MB).'),
        'too_small': _('Memory limit is too small.'),
    }
    help_text = _('Memory limit per test measured in mebibytes (i. e. 64 or 256).')
    int_to_float_ratio = 1024 * 1024
    max_float_value = 2048

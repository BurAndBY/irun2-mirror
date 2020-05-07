import six

from django.utils.functional import lazy
from django.utils.translation import gettext
from django.utils.encoding import smart_text
from django.utils.translation import gettext_lazy as _

FAKE_MESSAGES = [
    _('Ex.'),
    _('Format'),
]


def _format_example(key, value):
    return '{}: {}'.format(smart_text(gettext(key)), value)


def _ex(value):
    return lazy(_format_example, six.text_type)('Ex.', value)


def _fmt(value):
    return lazy(_format_example, six.text_type)('Format', value)


class Example(object):
    def __init__(self, en_value, local_value=None):
        self._en_value = en_value
        self._local_value = local_value
        self.localized = False

    @property
    def value(self):
        if self.localized and (self._local_value is not None):
            return self._local_value
        return self._en_value

    def __str__(self):
        return str(_ex(self.value))


class LocalizeMixin(object):
    fill_in_en = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.help_text, Example):
                field.help_text.localized = not self.fill_in_en

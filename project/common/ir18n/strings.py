import json

from django.conf import settings
from django.utils import translation

from common.locales.best import find_best_value


def looks_like_json(value):
    return value.startswith('{') and value.endswith('}')


class LazyI18nString:
    def __init__(self, data=''):
        if not isinstance(data, (str, dict)):
            raise TypeError('LazyI18nString can contain either str or dict')
        self.data = data

    def __repr__(self):
        return '<LazyI18nString: %s>' % repr(self.data)

    def __str__(self):
        return self.localize(translation.get_language() or settings.LANGUAGE_CODE)

    def __bool__(self):
        return bool(self.data)

    def values(self):
        if isinstance(self.data, dict):
            yield from self.data.values()
        else:
            yield self.data

    def items(self):
        if isinstance(self.data, dict):
            yield from self.data.items()
        else:
            yield ('', self.data)

    def localize(self, lng):
        if isinstance(self.data, dict):
            return find_best_value(self.data.items(), lng)
        else:
            return self.data

    def serialize(self):
        if isinstance(self.data, dict):
            return json.dumps(self.data, sort_keys=False, ensure_ascii=False, separators=(',', ':'))
        else:
            return self.data

    @staticmethod
    def deserialize(value):
        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError('Value to deserialize must be a string, got {}'.format(type(value).__name__))

        if looks_like_json(value):
            return LazyI18nString(json.loads(value))
        else:
            return LazyI18nString(value)

    def __eq__(self, other):
        if isinstance(other, LazyI18nString):
            return self.data == other.data
        return False

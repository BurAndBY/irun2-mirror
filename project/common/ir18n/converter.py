from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from .strings import LazyI18nString
from .strings import looks_like_json


class Converter:
    @staticmethod
    def i18nstr_to_list(value):
        if not isinstance(value, LazyI18nString):
            raise TypeError('LazyI18nString is expected')

        if value.data is None:
            return []
        if isinstance(value.data, dict):
            return [(k, v) for k, v in value.data.items()]
        if isinstance(value.data, str):
            return [('', value.data)]

        raise ValueError('Unexpected value inside LazyI18nString')

    @staticmethod
    def list_to_i18nstr(value, allowed_langs):
        if not isinstance(value, list):
            raise TypeError('list of pairs is expected')

        if len(value) == 1:
            k, v = next(iter(value))
            if not k:
                if looks_like_json(v):
                    raise ValidationError(
                        _('Default translation cannot start with { and end with }'),
                        code='looks_like_json'
                    )
                return LazyI18nString(v)

        data = {}
        for k, v in value:
            if not v:
                continue
            if not k:
                raise ValidationError(
                    _('Choosing the language is required unless there is a single translation'),
                    code='no_lang'
                )
            if k not in allowed_langs:
                raise ValidationError(
                    _('Unknown language %(lang)s'),
                    code='unknown_lang',
                    params={'lang': k}
                )
            if k in data:
                raise ValidationError(
                    _('Multiple translations for %(lang)s language'),
                    code='multiple',
                    params={'lang': k}
                )
            data[k] = v

        if data:
            return LazyI18nString(data)

        return LazyI18nString()

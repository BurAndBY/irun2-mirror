from django.core import validators

from .strings import LazyI18nString


class MaxLengthValidator(validators.MaxLengthValidator):
    def clean(self, x):
        if not isinstance(x, LazyI18nString):
            raise TypeError('LazyI18nString is expected')
        return super().clean(x.serialize())

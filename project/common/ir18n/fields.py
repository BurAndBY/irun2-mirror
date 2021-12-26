import django
import json
from django.conf import settings
from django.db import models

from .forms import IR18nFormField, IR18nTextInput
from .strings import LazyI18nString
from .validators import MaxLengthValidator


class IR18nCharField(models.CharField):
    form_class = IR18nFormField
    widget = IR18nTextInput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert len(self.validators) == 1
        self.validators = [MaxLengthValidator(self.max_length)]

    def to_python(self, value):
        if isinstance(value, LazyI18nString):
            return value
        return LazyI18nString.deserialize(value)

    def get_prep_value(self, value):
        if isinstance(value, LazyI18nString):
            value = value.serialize()
        return value

    def from_db_value(self, value, expression, connection):
        return LazyI18nString.deserialize(value)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)

    def formfield(self, **kwargs):
        defaults = {'form_class': self.form_class, 'widget': self.widget}
        defaults.update(kwargs)
        return super().formfield(**defaults)

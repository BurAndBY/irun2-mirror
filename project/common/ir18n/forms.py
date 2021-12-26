from django import forms
from django.conf import settings

from .converter import Converter
from .strings import LazyI18nString
from .validators import MaxLengthValidator


class IR18nTextInput(forms.Widget):
    template_name = 'common/ir18n/widget.html'
    allowed_langs = []

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['allowed_langs'] = self.allowed_langs
        return context

    def format_value(self, value):
        return value

    def value_omitted_from_data(self, data, files, name):
        return False

    def value_from_datadict(self, data, files, name):
        res = []
        idx = 0
        while True:
            lang = data.get('{}_lang_{}'.format(name, idx))
            value = data.get('{}_value_{}'.format(name, idx))
            if lang is not None and value is not None:
                res.append((lang, value))
                idx += 1
            else:
                break
        return res


class IR18nFormField(forms.Field):
    widget = IR18nTextInput

    def __init__(self, allowed_langs=None, max_length=None, **kwargs):
        super().__init__(**kwargs)

        self.allowed_langs = allowed_langs or settings.MODEL_LANGUAGES

        if max_length is not None:
            self.validators.append(MaxLengthValidator(int(max_length)))

        self.widget.allowed_langs = self.allowed_langs

    def prepare_value(self, value):
        if isinstance(value, LazyI18nString):
            return Converter.i18nstr_to_list(value)
        return value

    def to_python(self, value):
        return Converter.list_to_i18nstr(value, self.allowed_langs)

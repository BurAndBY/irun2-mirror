from django.db.models.fields import CharField
from django.utils.text import format_lazy
from django.utils.translation import get_language_info
from django.utils.translation import gettext_lazy as _

LANGUAGES = ['en', 'ru', 'lt', 'be']

CHOICES = [
    (lang, format_lazy('{} ({})', get_language_info(lang)['name_translated'], lang))
    for lang in LANGUAGES
]

CHOICES_EX = [('', _('Not set'))] + CHOICES


class LanguageField(CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 2)
        kwargs.setdefault('choices', CHOICES_EX)
        super(CharField, self).__init__(*args, **kwargs)

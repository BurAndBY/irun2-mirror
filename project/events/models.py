# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language

MAX_TITLE_LENGTH = 100


def _localize_string(local_value, en_value):
    if not local_value:
        return en_value
    if not en_value:
        return local_value
    return en_value if (get_language() == 'en') else local_value


class Event(models.Model):
    slug = models.SlugField(_('name for URL'), help_text=_('Short Latin name to use in page links'), unique=True)

    local_name = models.CharField(_('name in local language'), max_length=MAX_TITLE_LENGTH, blank=True)
    en_name = models.CharField(_('name in English'), max_length=MAX_TITLE_LENGTH, blank=True)

    local_description = models.TextField(_('descripion in local language'), blank=True)
    en_description = models.TextField(_('descripion in English'), blank=True)

    is_registration_available = models.BooleanField(_('registration is available'), default=False, blank=True)

    @property
    def name(self):
        return _localize_string(self.local_name, self.en_name)

    @property
    def description(self):
        return _localize_string(self.local_description, self.en_description)

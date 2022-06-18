# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language

from contests.models import Contest
from storage.models import FileMetadata
from users.models import UserFolder

MAX_TITLE_LENGTH = 100


def _localize_string(local_value, en_value):
    if not local_value:
        return en_value
    if not en_value:
        return local_value
    return en_value if (get_language() == 'en') else local_value


class RegistrationMode(object):
    COACH_AND_TEAMS = 1
    INDIVIDUAL = 2
    INDIVIDUAL_SCHOOL = 3
    INDIVIDUAL_HUAWEI = 4

    CHOICES = (
        (COACH_AND_TEAMS, _('Coach and teams')),
        (INDIVIDUAL, _('Individual')),
        (INDIVIDUAL_SCHOOL, _('Individual school')),
        (INDIVIDUAL_HUAWEI, _('Individual for Huawei')),
    )


class LogoStyle(object):
    FILE = 1
    ICPC = 2

    CHOICES = (
        (FILE, _('File')),
        (ICPC, 'ICPC'),
    )


class Event(models.Model):
    slug = models.SlugField(_('name for URL'), help_text=_('Short Latin name to use in page links'), unique=True)

    local_name = models.CharField(_('name in local language'), max_length=MAX_TITLE_LENGTH, blank=True)
    en_name = models.CharField(_('name in English'), max_length=MAX_TITLE_LENGTH, blank=True)

    local_description = models.TextField(_('descripion in local language'), blank=True)
    en_description = models.TextField(_('descripion in English'), blank=True)

    is_registration_available = models.BooleanField(_('registration is available'), default=False, blank=True)
    registration_mode = models.IntegerField(_('registration mode'), choices=RegistrationMode.CHOICES, default=RegistrationMode.COACH_AND_TEAMS)

    fill_forms_in_en = models.BooleanField(_('the forms are filled in English'), default=True, blank=False)

    logo_style = models.IntegerField(_('logo style'), choices=LogoStyle.CHOICES, default=None, null=True, blank=True)
    logo_file = models.ForeignKey(FileMetadata, null=True, on_delete=models.SET_NULL, verbose_name=_('image file'))

    auto_create_users = models.BooleanField(_('create users automatically'), default=False, blank=True)
    user_folder = models.ForeignKey(UserFolder, verbose_name=_('user folder'), on_delete=models.SET_NULL, null=True, blank=True)
    username_pattern = models.CharField(_('username pattern'), max_length=30, blank=True)
    password_generation_algo = models.CharField(max_length=16, blank=True)
    last_created_number = models.IntegerField(default=0)
    contest = models.ForeignKey(Contest, verbose_name=_('Contest'), on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def name(self):
        return _localize_string(self.local_name, self.en_name)

    @property
    def description(self):
        return _localize_string(self.local_description, self.en_description)

    @property
    def registering_coaches(self):
        return self.registration_mode == RegistrationMode.COACH_AND_TEAMS

    @property
    def school_only(self):
        return self.registration_mode == RegistrationMode.INDIVIDUAL_SCHOOL


class Page(models.Model):
    event = models.ForeignKey(Event, null=False, on_delete=models.CASCADE)
    slug = models.SlugField(_('name for URL'), help_text=_('Short Latin name to use in page links'))

    when = models.DateTimeField(_('Time'), default=timezone.now)
    is_public = models.BooleanField(_('show on the main page'), default=True, blank=True)

    local_name = models.CharField(_('name in local language'), max_length=MAX_TITLE_LENGTH, blank=True)
    en_name = models.CharField(_('name in English'), max_length=MAX_TITLE_LENGTH, blank=True)

    local_content = models.TextField(_('descripion in local language'), blank=True)
    en_content = models.TextField(_('descripion in English'), blank=True)

    @property
    def name(self):
        return _localize_string(self.local_name, self.en_name)

    @property
    def content(self):
        return _localize_string(self.local_content, self.en_content)

    class Meta:
        unique_together = ('event', 'slug')

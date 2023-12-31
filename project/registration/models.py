# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid
import shortuuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from events.models import Event

CONTESTANTS_PER_TEAM = 3

MAX_NAME_LENGTH = 50
MAX_ENUM_LENGTH = 16
MAX_TITLE_LENGTH = 255
MAX_EMAIL_LENGTH = 100
MAX_UNIVERSITY_LENGTH = 120
MAX_ADDRESS_LENGTH = 255
MAX_COUNTRY_LENGTH = 32
MAX_TEXT_LENGTH = 2000


PARTICIPATION_VENUE_CHOICES = [
    ('OWN', _('Own university')),
    ('BSU', _('Belarusian State University')),
    ('NEARBY', _('Ask about near venues')),
]

PARTICIPATION_TYPE_CHOICES = [
    ('OFFICIAL', _('Official (diplomas, personal invitation)')),
    ('HORS_CONCOURS', _('Hors concours')),
]

STUDY_PROGRAM_CHOICES = [
    ('BACHELOR', _('Bachelor')),
    ('SPECIALIST', _('Specialist')),
    ('MASTER', _('Master')),
    ('PHD', _('PhD')),
]

SEX_CHOICES = [
    ('FEMALE', _('Female')),
    ('MALE', _('Male')),
]


class IcpcCoach(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('e-mail'), max_length=MAX_EMAIL_LENGTH)
    first_name = models.CharField(_('first name'), max_length=MAX_NAME_LENGTH)
    last_name = models.CharField(_('last name'), max_length=MAX_NAME_LENGTH)
    university = models.CharField(_('university'), max_length=MAX_UNIVERSITY_LENGTH)
    faculty = models.CharField(_('faculty'), max_length=MAX_UNIVERSITY_LENGTH, blank=True)
    year_of_study = models.PositiveIntegerField(_('Year of study'), null=True, blank=True)
    group = models.PositiveIntegerField(_('Group number'), null=True, blank=True)
    is_confirmed = models.BooleanField(_('Confirmed'), null=False, blank=True, default=True)
    postal_address = models.CharField(_('Postal address'), max_length=MAX_ADDRESS_LENGTH, blank=True)
    phone_number = models.CharField(_('Phone number'), max_length=16, blank=True, validators=[
        RegexValidator(regex=r'\+\d{7,15}')
    ])
    country = models.CharField(_('Country'), max_length=MAX_COUNTRY_LENGTH, blank=True)
    achievements = models.TextField(_('Achievements'), max_length=MAX_TEXT_LENGTH, blank=True)
    extra_info = models.TextField(_('Extra information'), max_length=MAX_TEXT_LENGTH, blank=True)

    @property
    def full_name(self):
        full_name = '{} {}'.format(self.first_name, self.last_name)
        return full_name.strip()

    @property
    def human_readable_id(self):
        return shortuuid.encode(self.id)

    class Meta:
        unique_together = ('event', 'email')


class IcpcTeam(models.Model):
    coach = models.ForeignKey(IcpcCoach, on_delete=models.CASCADE)
    name = models.CharField(_('team name'), max_length=MAX_TITLE_LENGTH)
    participation_venue = models.CharField(_('participation venue'), max_length=MAX_ENUM_LENGTH, choices=PARTICIPATION_VENUE_CHOICES)
    participation_type = models.CharField(_('participation type'), max_length=MAX_ENUM_LENGTH, choices=PARTICIPATION_TYPE_CHOICES)


class IcpcContestant(models.Model):
    team = models.ForeignKey(IcpcTeam, on_delete=models.CASCADE)
    email = models.EmailField(_('e-mail'), max_length=MAX_EMAIL_LENGTH)
    first_name = models.CharField(_('first name'), max_length=MAX_NAME_LENGTH)
    last_name = models.CharField(_('last name'), max_length=MAX_NAME_LENGTH)
    date_of_birth = models.DateField(_('date of birth'))
    study_program = models.CharField(_('study program'), max_length=MAX_ENUM_LENGTH, choices=STUDY_PROGRAM_CHOICES)
    program_start_year = models.IntegerField(_('program start year'))
    graduation_year = models.IntegerField(_('graduation year'))
    sex = models.CharField(_('sex'), max_length=MAX_ENUM_LENGTH, choices=SEX_CHOICES)


class CreatedUser(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    coach = models.ForeignKey(IcpcCoach, null=True, on_delete=models.CASCADE)
    team = models.ForeignKey(IcpcTeam, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    password = models.CharField(max_length=100)

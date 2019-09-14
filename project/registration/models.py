# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid
import shortuuid

from django.db import models
from django.utils.translation import ugettext_lazy as _

from events.models import Event

CONTESTANTS_PER_TEAM = 3

MAX_NAME_LENGTH = 50
MAX_ENUM_LENGTH = 16
MAX_TITLE_LENGTH = 255
MAX_EMAIL_LENGTH = 100

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
    email = models.EmailField(_('e-mail'), unique=True, max_length=MAX_EMAIL_LENGTH)
    first_name = models.CharField(_('first name'), max_length=MAX_NAME_LENGTH)
    last_name = models.CharField(_('last name'), max_length=MAX_NAME_LENGTH)
    university = models.CharField(_('university'), max_length=MAX_NAME_LENGTH)

    @property
    def full_name(self):
        full_name = '{} {}'.format(self.first_name, self.last_name)
        return full_name.strip()

    @property
    def human_readable_id(self):
        return shortuuid.encode(self.id)


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

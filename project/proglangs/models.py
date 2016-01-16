from django.db import models
from django.utils.translation import ugettext_lazy as _


# Create your models here.
class Compiler(models.Model):
    UNKNOWN = ''
    C = 'c'
    CPP = 'cpp'
    JAVA = 'java'
    PASCAL = 'pas'
    DELPHI = 'dpr'
    PYTHON = 'py'
    CSHARP = 'cs'

    LANGUAGE_CHOICES = (
        (UNKNOWN, _('Unknown')),
        (C, 'C'),
        (CPP, 'C++'),
        (JAVA, 'Java'),
        (PASCAL, 'Pascal'),
        (DELPHI, 'Delphi'),
        (PYTHON, 'Python'),
        (CSHARP, 'C#'),
    )

    handle = models.CharField(_('string identifier'), max_length=30, unique=True)
    language = models.CharField(_('language'), max_length=8, choices=LANGUAGE_CHOICES, default=UNKNOWN, blank=True)
    description = models.CharField(_('description'), max_length=255, blank=True)
    legacy = models.BooleanField(_('compiler is considered legacy'), default=False)

    def __unicode__(self):
        return self.description

    class Meta:
        ordering = ['description']

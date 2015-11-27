from django.db import models


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
        (UNKNOWN, 'Unknown'),
        (C, 'C'),
        (CPP, 'C++'),
        (JAVA, 'Java'),
        (PASCAL, 'Pascal'),
        (DELPHI, 'Delphi'),
        (PYTHON, 'Python'),
        (CSHARP, 'C#'),
    )

    handle = models.CharField(max_length=30, unique=True)
    language = models.CharField(max_length=8, choices=LANGUAGE_CHOICES, default=UNKNOWN, blank=True)
    description = models.CharField(max_length=255, blank=True)
    legacy = models.BooleanField(default=False)

    def __unicode__(self):
        return self.description

    class Meta:
        ordering = ['description']

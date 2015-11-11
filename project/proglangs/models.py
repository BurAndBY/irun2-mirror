from django.db import models


# Create your models here.
class ProgrammingLanguage(models.Model):
    UNKNOWN = ''
    CPP = 'cpp'
    JAVA = 'java'
    PASCAL = 'pascal'
    DELPHI = 'delphi'
    PYTHON = 'py'
    CSHARP = 'cs'

    FAMILY_CHOICES = (
        (UNKNOWN, 'Unknown'),
        (CPP, 'C/C++'),
        (JAVA, 'Java'),
        (PASCAL, 'Pascal'),
        (DELPHI, 'Delphi'),
        (PYTHON, 'Python'),
        (CSHARP, 'C#'),
    )

    handle = models.CharField(max_length=30, unique=True)
    family = models.CharField(max_length=8, choices=FAMILY_CHOICES, default=UNKNOWN, blank=True)
    description = models.CharField(max_length=255, blank=True)
    legacy = models.BooleanField(default=False)

    def __unicode__(self):
        return self.description

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from proglangs.langlist import ProgrammingLanguage


@python_2_unicode_compatible
class Compiler(models.Model):
    handle = models.CharField(_('string identifier'), max_length=30, unique=True)
    language = models.CharField(_('language'), max_length=8, choices=ProgrammingLanguage.CHOICES, default=ProgrammingLanguage.UNKNOWN, blank=True)
    description = models.CharField(_('description'), max_length=255, blank=True)
    default_for_courses = models.BooleanField(_('compiler is enabled by default in new courses'), default=False)
    default_for_contests = models.BooleanField(_('compiler is enabled by default in new contests'), default=False)

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['description']


class CompilerDetails(models.Model):
    compiler = models.OneToOneField(Compiler, on_delete=models.CASCADE, primary_key=True)
    compile_command = models.CharField(_('compile command'), max_length=1023, blank=True)
    run_command = models.CharField(_('run command'), max_length=1023, blank=True)

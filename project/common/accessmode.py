from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class AccessMode(object):
    READ = 1
    WRITE = 2

    CHOICES = (
        (READ, _('Read')),
        (WRITE, _('Write')),
    )


class BaseAccess(models.Model):
    mode = models.IntegerField(choices=AccessMode.CHOICES)
    when_granted = models.DateTimeField(auto_now=True)
    who_granted = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', null=True, on_delete=models.SET_NULL)

    class Meta:
        abstract = True

from django.conf import settings
from django.db import models

from .accessmode import AccessMode


class BaseAccess(models.Model):
    mode = models.IntegerField(choices=AccessMode.CHOICES)
    when_granted = models.DateTimeField(auto_now=True)
    who_granted = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', null=True, on_delete=models.SET_NULL)

    class Meta:
        abstract = True

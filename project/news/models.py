from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class NewsMessage(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    when = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(_('subject'), blank=True, max_length=255)
    body = models.TextField(_('message body'), max_length=65535)
    is_public = models.BooleanField(_('show on the main page'), default=True, blank=True)

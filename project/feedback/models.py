from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from storage.models import FileMetadata


class FeedbackMessage(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    email = models.EmailField(blank=True)
    when = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(_('subject'), blank=True, max_length=255)
    body = models.TextField(_('message body'), max_length=1024)
    attachment = models.ForeignKey(FileMetadata, null=True, on_delete=models.SET_NULL, verbose_name=_('attachment'))

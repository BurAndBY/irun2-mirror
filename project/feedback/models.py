from django.db import models
from django.conf import settings

from storage.models import FileMetadata


class FeedbackMessage(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    email = models.EmailField(blank=True)
    when = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(blank=True, max_length=255)
    body = models.TextField(max_length=1024)
    attachment = models.ForeignKey(FileMetadata, null=True, on_delete=models.SET_NULL)

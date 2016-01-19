from django.db import models
from .storage import ResourceIdField


class FileMetadata(models.Model):
    filename = models.CharField(max_length=255)
    size = models.IntegerField()
    resource_id = ResourceIdField()

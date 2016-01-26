from django.db import models
from .storage import ResourceIdField


class FileMetadataBase(models.Model):
    filename = models.CharField(max_length=255)
    size = models.IntegerField()
    resource_id = ResourceIdField()

    class Meta:
        abstract = True


class FileMetadata(FileMetadataBase):
    pass

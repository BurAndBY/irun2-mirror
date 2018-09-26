from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from .storage import ResourceIdField
from .validators import validate_filename


@python_2_unicode_compatible
class FileMetadataBase(models.Model):
    filename = models.CharField(_('Filename'), max_length=255, validators=[validate_filename])
    size = models.IntegerField()
    resource_id = ResourceIdField()

    class Meta:
        abstract = True

    def __str__(self):
        return self.filename


class FileMetadata(FileMetadataBase):
    pass

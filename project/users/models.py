from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey


# Create your models here.
class UserFolder(MPTTModel):
    name = models.CharField(_('name'), max_length=64)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)

    def __unicode__(self):
        return self.name

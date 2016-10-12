from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey

from proglangs.models import Compiler
from storage.storage import ResourceIdField


# Create your models here.
class UserFolder(MPTTModel):
    name = models.CharField(_('name'), max_length=64)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    description = models.CharField(_('description'), max_length=255, blank=True)

    def __unicode__(self):
        return self.name


class UserProfile(models.Model):
    PERSON = 1
    TEAM = 2

    KIND_CHOICES = (
        (PERSON, _('Person')),
        (TEAM, _('Team')),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, on_delete=models.CASCADE)  # required
    folder = models.ForeignKey(UserFolder, verbose_name=_('folder'), on_delete=models.PROTECT, null=True, blank=True)
    patronymic = models.CharField(_('patronymic'), max_length=30, blank=True)
    needs_change_password = models.BooleanField(_('password needs to be changed by user'), null=False, default=False)
    description = models.CharField(_('description'), max_length=255, blank=True)
    last_used_compiler = models.ForeignKey(Compiler, verbose_name=_('last used compiler'), on_delete=models.SET_NULL, null=True, blank=True)
    has_api_access = models.BooleanField(_('API access'), default=False)
    photo = ResourceIdField(null=True)
    photo_thumbnail = ResourceIdField(null=True)
    kind = models.IntegerField(_('kind'), choices=KIND_CHOICES, default=PERSON)
    members = models.CharField(_('members'), max_length=255, blank=True)

    def is_team(self):
        return self.kind == UserProfile.TEAM


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=settings.AUTH_USER_MODEL)

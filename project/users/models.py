from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey

from cauth.acl.models import BaseAccess
from proglangs.models import Compiler
from storage.storage import ResourceIdField


@python_2_unicode_compatible
class UserFolder(MPTTModel):
    name = models.CharField(_('name'), max_length=64)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', db_index=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    description = models.CharField(_('description'), max_length=255, blank=True)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class AdminGroup(models.Model):
    name = models.CharField(_('name'), max_length=64)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)

    def __str__(self):
        return self.name


class UserFolderAccess(BaseAccess):
    folder = models.ForeignKey(UserFolder, on_delete=models.CASCADE)
    group = models.ForeignKey(AdminGroup, on_delete=models.CASCADE, related_name='+')

    class Meta:
        unique_together = ('folder', 'group')


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
    photo = ResourceIdField(null=True)
    photo_thumbnail = ResourceIdField(null=True)
    kind = models.IntegerField(_('kind'), choices=KIND_CHOICES, default=PERSON)
    members = models.CharField(_('members'), max_length=255, blank=True)
    can_change_name = models.BooleanField(_('user is allowed to change name'), null=False, default=False)
    can_change_password = models.BooleanField(_('user is allowed to change password'), null=False, default=True)
    has_access_to_problems = models.BooleanField(_('user was explicitly granted access to certain problems'), default=False)
    has_access_to_quizzes = models.BooleanField(_('user was explicitly granted access to certain quiz categories'), default=False)
    has_access_to_admin = models.BooleanField(_('user has access to administrative sections'), default=False)

    def is_team(self):
        return self.kind == UserProfile.TEAM


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


post_save.connect(create_user_profile, sender=settings.AUTH_USER_MODEL)

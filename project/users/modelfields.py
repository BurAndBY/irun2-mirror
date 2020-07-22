from django.db import models
from django.utils.translation import ugettext_lazy as _

from users.models import AdminGroup
from users.fields import OwnerGroupField as FormField


class OwnerGroupField(models.ForeignKey):
    def __init__(self, **kwargs):
        kwargs.setdefault('to', AdminGroup)
        kwargs.setdefault('on_delete', models.SET_NULL)
        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)
        kwargs.setdefault('default', None)
        kwargs.setdefault('verbose_name', _('owner'))
        super().__init__(**kwargs)

    def formfield(self, **kwargs):
        defaults = {
            'form_class': FormField,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)


def is_instance_owned(model_instance, user):
    if user.is_staff:
        return True
    if user.is_admin:
        if (model_instance.owner_id is not None) and (model_instance.owner_id in user.admingroup_ids):
            return True
    return False

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from common.tree.fields import ThreePanelModelMultipleChoiceField

from users.loader import UserFolderLoader


class UsernameField(forms.CharField):
    widget = forms.TextInput(attrs={'placeholder': _('Username')})

    default_error_messages = {
        'does_not_exist': _('User %(username)s not found.'),
    }

    def to_python(self, value):
        value = super(UsernameField, self).to_python(value)

        user_model = get_user_model()
        user_id = user_model.objects.filter(username=value).values_list('id', flat=True).first()
        if user_id is None:
            raise forms.ValidationError(self.error_messages['does_not_exist'], params={'username': value})

        return user_id


class ThreePanelUserMultipleChoiceField(ThreePanelModelMultipleChoiceField):
    loader_cls = UserFolderLoader

    @classmethod
    def label_from_instance(cls, obj):
        return obj.get_full_name()

    @classmethod
    def build_pk2folders(cls, pks):
        pk2folders = {}
        for pk, folder_id in get_user_model().objects.\
                filter(pk__in=pks).\
                values_list('pk', 'userprofile__folder_id').\
                order_by():
            pk2folders.setdefault(pk, [folder_id])
        return pk2folders

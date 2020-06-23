# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from users.fields import ThreePanelUserMultipleChoiceField
from users.models import AdminGroup
from common.tree.fields import FOLDER_ID_PLACEHOLDER
from common.tree.fields import TwoPanelModelMultipleChoiceField


class TwoPanelUserMultipleChoiceField(TwoPanelModelMultipleChoiceField):
    @classmethod
    def label_from_instance(cls, obj):
        return obj.get_full_name()


class AdminGroupForm(forms.ModelForm):
    class Meta:
        model = AdminGroup
        fields = ['name', 'users']

    users = ThreePanelUserMultipleChoiceField(label=_('Users'), required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['users'].configure(
            initial=None,
            user=user,
            url_template=reverse('users:admingroups:users_json_list', kwargs={'folder_id_or_root': FOLDER_ID_PLACEHOLDER}),
        )

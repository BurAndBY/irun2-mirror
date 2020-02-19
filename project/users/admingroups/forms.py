# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.contrib import auth
from django.utils.translation import ugettext_lazy as _

from users.models import UserFolder, AdminGroup
from common.tree.fields import TwoPanelModelMultipleChoiceField


class TwoPanelUserMultipleChoiceField(TwoPanelModelMultipleChoiceField):
    @classmethod
    def label_from_instance(cls, obj):
        return obj.get_full_name()


class AdminGroupForm(forms.ModelForm):
    class Meta:
        model = AdminGroup
        fields = ['name', 'users']

    users = TwoPanelUserMultipleChoiceField(label=_('Users'), required=False,
                                            model=auth.get_user_model(), folder_model=UserFolder,
                                            url_pattern='users:admingroups:users_json_list')

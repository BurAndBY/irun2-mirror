# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from common.tree.fields import FolderChoiceField

from cauth.acl.accessmode import AccessMode

from users.loader import UserFolderLoader


class MoveUsersForm(forms.Form):
    folder = FolderChoiceField(label=_('Destination folder'), loader_cls=UserFolderLoader,
                               required=False, required_mode=AccessMode.WRITE, none_means_not_set=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['folder'].user = user


'''
User search
'''


class UserSearchForm(forms.Form):
    query = forms.CharField(required=False)
    staff = forms.BooleanField(label=_('Staff only'), required=False)

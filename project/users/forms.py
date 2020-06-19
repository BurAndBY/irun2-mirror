# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from common.tree.mptt_fields import OrderedTreeNodeChoiceField

from users.models import UserFolder


class MoveUsersForm(forms.Form):
    folder = OrderedTreeNodeChoiceField(label=_('Destination folder'), queryset=None, required=False)

    def __init__(self, *args, **kwargs):
        super(MoveUsersForm, self).__init__(*args, **kwargs)
        self.fields['folder'].queryset = UserFolder.objects.all()


'''
User search
'''


class UserSearchForm(forms.Form):
    query = forms.CharField(required=False)
    staff = forms.BooleanField(label=_('Staff only'), required=False)

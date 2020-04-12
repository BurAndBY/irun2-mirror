# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import auth
from django.core.files.base import ContentFile

from common.fakefile import FakeFile
from common.tree.mptt_fields import OrderedTreeNodeChoiceField

from users.models import UserFolder, UserProfile
from users.photo import generate_thumbnail_file


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


'''
User profile: main
'''


class UserMainForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = ['is_active', 'username']


class UserProfileMainForm(forms.ModelForm):
    folder = OrderedTreeNodeChoiceField(label=_('Folder'), queryset=None, required=False)

    class Meta:
        model = UserProfile
        fields = ['folder']

    def __init__(self, *args, **kwargs):
        super(UserProfileMainForm, self).__init__(*args, **kwargs)
        self.fields['folder'].queryset = UserFolder.objects.all()


'''
User profile: update
'''


class UserForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = ['email', 'last_name', 'first_name']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['patronymic', 'needs_change_password', 'kind', 'members', 'description']

        help_texts = {
            'needs_change_password': _('User will see a warning message until he sets a new password. '
                                       'This prevents usage of insecure default passwords.')
        }
        widgets = {
            'kind': forms.RadioSelect
        }


'''
User profile: permissions
'''


class UserPermissionsForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = ['is_staff']


class UserProfilePermissionsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'can_change_name',
            'can_change_password',
            'has_access_to_problems',
            'has_access_to_quizzes',
            'has_access_to_admin',
        ]


'''
Photos
'''


class PhotoForm(forms.Form):
    upload = forms.FileField(label=_('Photo'), required=False, help_text=_('Select JPEG image.'))

    def clean(self):
        cleaned_data = super(PhotoForm, self).clean()
        upload = cleaned_data.get('upload')
        if (upload) and (type(upload) is not FakeFile):
            thumb = None
            try:
                thumb = generate_thumbnail_file(upload)
            except forms.ValidationError as e:
                self.add_error('upload', e)
            cleaned_data['thumbnail'] = ContentFile(thumb, name='thumb.jpg')

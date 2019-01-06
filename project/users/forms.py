# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import zipfile

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import auth
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile

from common.fakefile import FakeFile
from common.mptt_fields import OrderedTreeNodeChoiceField

from users.models import UserFolder, UserProfile
from users.photo import generate_thumbnail_file, generate_thumbnail_blob


class MassUserInitForm(forms.Form):
    tsv = forms.CharField(widget=forms.Textarea, required=False)


class MassUserPasswordForm(forms.Form):
    password = forms.CharField(required=True)


class MassUserSingleForm(forms.Form):
    username = forms.CharField()
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)


class CreateFolderForm(forms.Form):
    name = forms.CharField(label=_('Folder name'), widget=forms.TextInput(attrs={'autofocus': 'autofocus'}))


class CreateUserForm(UserCreationForm):
    pass


class CreateUsersMassForm(forms.Form):
    MODE_CHOICES = (
        ('students', _('Students: “[username] [last name] [first name]” or “[username] [last name] [first name] [patronymic]”')),
        ('acm', _('Teams: “[username] [team name]”')),
    )

    mode = forms.ChoiceField(label=_('Mode'), choices=MODE_CHOICES)
    tsv = forms.CharField(widget=forms.Textarea, required=True,
                          label=_('Data about users'),
                          help_text=_('Enter lines in the given format.'))
    password = forms.CharField(required=True, label=_('Password'))

    def _parse_user_line(self, line, mode, number):
        first_name = ''
        last_name = ''
        patronymic = ''

        if mode == 'students':
            tokens = line.split()
            if len(tokens) == 3:
                username, last_name, first_name = tokens
            elif len(tokens) == 4:
                username, last_name, first_name, patronymic = tokens
            else:
                raise forms.ValidationError(_('Line %(number)s does not match the template.'),
                                            code='tokens', params={'number': number + 1})
        elif mode == 'acm':
            tokens = line.split(None, 1)
            if len(tokens) == 1:
                username, = tokens
            else:
                username, first_name = tokens

        user_model = auth.get_user_model()
        user = user_model(username=username, first_name=first_name, last_name=last_name)
        userprofile = UserProfile(patronymic=patronymic, needs_change_password=True, folder=None)
        return user, userprofile

    def clean(self):
        cleaned_data = super(CreateUsersMassForm, self).clean()
        password = cleaned_data.get('password')
        tsv = cleaned_data.get('tsv')
        mode = cleaned_data.get('mode')

        if password is not None and tsv is not None and mode is not None:
            hashed_password = make_password(password)
            pairs = []
            usernames = set()
            for number, line in enumerate(tsv.splitlines()):
                line = line.strip()
                if not line:
                    continue
                user, userprofile = self._parse_user_line(line, mode, number)
                if user.username in usernames:
                    raise forms.ValidationError(_('User “%(username)s” is listed more than once.'),
                                                code='duplicate', params={'username': user.username})
                usernames.add(user.username)
                pairs.append((user, userprofile))

            errors = []
            for user, userprofile in pairs:
                try:
                    user.password = hashed_password
                    user.full_clean()

                    userprofile.full_clean(exclude=['user'])
                except forms.ValidationError as e:
                    errors.append(forms.ValidationError('{0}: {1}'.format(user.username, ' '.join(e.messages))))
            if errors:
                raise forms.ValidationError(errors)
            cleaned_data['pairs'] = pairs

        return cleaned_data


class UpdateProfileMassForm(forms.Form):
    FIELD_CHOICES = (
        ('password', _('Password')),
        ('team_name', _('Team name')),
        ('team_members', _('Team members')),
        ('full_name', _('Last name, first name, patronymic')),
    )

    field = forms.ChoiceField(label=_('Field to update'), choices=FIELD_CHOICES)
    tsv = forms.CharField(widget=forms.Textarea, required=True,
                          label=_('Data about users'),
                          help_text=_('Enter lines in the format of “[username] [value]”.'))

    def __init__(self, *args, **kwargs):
        self.folder_id = kwargs.pop('folder_id', None)
        super(UpdateProfileMassForm, self).__init__(*args, **kwargs)

    def clean_tsv(self):
        data = self.cleaned_data['tsv']
        user_model = auth.get_user_model()
        pairs = []

        for number, line in enumerate(data.splitlines()):
            line = line.strip()
            if not line:
                continue
            tokens = line.split(None, 1)
            if len(tokens) != 2:
                raise forms.ValidationError(_('Line %(number)s does not match the template.'),
                                            code='tokens', params={'number': number + 1})
            username, value = tokens

            qs = user_model.objects.filter(username=username)
            if self.folder_id is not None:
                qs = qs.filter(userprofile__folder_id=self.folder_id)

            user_id = qs.values_list('id', flat=True).first()
            if user_id is None:
                raise forms.ValidationError(_('User “%(username)s” does not exist.'),
                                            code='not_exists', params={'username': username})
            pairs.append((user_id, value))

        return pairs


class UploadPhotoMassForm(forms.Form):
    upload = forms.FileField(label=_('ZIP-archive'), required=True, widget=forms.FileInput)

    def __init__(self, *args, **kwargs):
        self.folder_id = kwargs.pop('folder_id', None)
        super(UploadPhotoMassForm, self).__init__(*args, **kwargs)

    def clean_upload(self):
        upload = self.cleaned_data.get('upload')

        # map: user_id -> (photo, photo_thumbnail) as blobs
        result = {}

        user_model = auth.get_user_model()
        usernames = {}
        for user_id, username in user_model.objects.filter(userprofile__folder_id=self.folder_id).values_list('pk', 'username'):
            usernames[username] = user_id

        try:
            with zipfile.ZipFile(upload, 'r', allowZip64=True) as myzip:
                for filename in myzip.namelist():
                    if '/' in filename:
                        raise forms.ValidationError(_('Archive should not contain subdirectories.'))
                    name, extension = os.path.splitext(filename)
                    if extension != '.jpg':
                        raise forms.ValidationError(_('File extension %(ext)s is not supported.'), params={'ext': extension})
                    if name not in usernames:
                        raise forms.ValidationError(_('User %(username)s is not found.'), params={'username': name})

                    photo = myzip.read(filename)
                    photo_thumbnail = generate_thumbnail_blob(photo)

                    result[usernames[name]] = (photo, photo_thumbnail)

        except zipfile.BadZipfile:
            raise forms.ValidationError(_('Archive format is not supported.'))

        return result


class IntranetBsuForm(forms.Form):
    FACULTY_CHOICES = (
        (3, _('Faculty of Applied Mathematics and Computer Science')),
        (2, _('Faculty of Radiophysics and Computer Technologies (RFE)')),
    )
    faculty = forms.TypedChoiceField(label=_('Faculty'), choices=FACULTY_CHOICES, required=True)
    include_archive = forms.BooleanField(label=_('Include archive'), required=False)
    group = forms.CharField(label=_('Group'), max_length=8, required=False)
    admission_year = forms.IntegerField(label=_('Admission year'), min_value=1990, required=False)
    skip_errors = forms.BooleanField(label=_('Skip errors'), help_text=_('On error, continue fetching photos for next users.'), required=False)


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
        fields = ['can_change_name', 'can_change_password', 'has_access_to_problems', 'has_access_to_quizzes']


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

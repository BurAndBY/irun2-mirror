# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import auth
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import make_password

from common.mptt_fields import OrderedTreeNodeChoiceField

from models import UserFolder, UserProfile


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
        ('students', _(u'Students: “[username] [last name] [first name]” or “[username] [last name] [first name] [patronymic]”')),
        ('acm', _(u'Teams: “[username] [team name]”')),
    )

    mode = forms.ChoiceField(label=_('Mode'), choices=MODE_CHOICES)
    tsv = forms.CharField(widget=forms.Textarea, required=True,
                          label=_('Data about users'),
                          help_text=_(u'Enter lines in the given format.'))
    password = forms.CharField(required=True, label=_('Password'))

    def _parse_user_line(self, line, mode, number):
        first_name = u''
        last_name = u''
        patronymic = u''

        if mode == 'students':
            tokens = line.split()
            if len(tokens) == 3:
                username, last_name, first_name = tokens
            elif len(tokens) == 4:
                username, last_name, first_name, patronymic = tokens
            else:
                raise forms.ValidationError(_(u'Line %(number)s does not match the template.'),
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
                    raise forms.ValidationError(_(u'User “%(username)s” is listed more than once.'),
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
                    errors.append(forms.ValidationError(u'{0}: {1}'.format(user.username, u' '.join(e.messages))))
            if errors:
                raise forms.ValidationError(errors)
            cleaned_data['pairs'] = pairs

        return cleaned_data


class ChangePasswordMassForm(forms.Form):
    tsv = forms.CharField(widget=forms.Textarea, required=True,
                          label=_('Data about users'),
                          help_text=_(u'Enter lines in the format of “[username] [password]”.'))

    def __init__(self, *args, **kwargs):
        self.folder_id = kwargs.pop('folder_id', None)
        super(ChangePasswordMassForm, self).__init__(*args, **kwargs)

    def clean_tsv(self):
        data = self.cleaned_data['tsv']
        user_model = auth.get_user_model()
        pairs = []

        for number, line in enumerate(data.splitlines()):
            line = line.strip()
            if not line:
                continue
            tokens = line.split()
            if len(tokens) != 2:
                raise forms.ValidationError(_(u'Line %(number)s does not match the template.'),
                                            code='tokens', params={'number': number + 1})
            username, password = tokens

            qs = user_model.objects.filter(username=username)
            if self.folder_id is not None:
                qs = qs.filter(userprofile__folder_id=self.folder_id)
            if not qs.exists():
                raise forms.ValidationError(_(u'User “%(username)s” does not exist.'),
                                            code='not_exists', params={'username': username})
            pairs.append((username, password))

        return pairs


class MoveUsersForm(forms.Form):
    folder = OrderedTreeNodeChoiceField(label=_('Destination folder'), queryset=UserFolder.objects.all(), required=False)

'''
User search
'''


class UserSearchForm(forms.Form):
    query = forms.CharField(required=False)
    staff = forms.BooleanField(label=_('Staff only'), required=False)


'''
User profile
'''


class UserForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = ['is_active', 'username', 'email', 'last_name', 'first_name']


class UserProfileForm(forms.ModelForm):
    folder = OrderedTreeNodeChoiceField(label=_('Folder'), queryset=UserFolder.objects.all(), required=False)

    class Meta:
        model = UserProfile
        fields = ['patronymic', 'folder', 'needs_change_password', 'description']

        help_texts = {
            'needs_change_password': _('User will see a warning message until he sets a new password. '
                                       'This prevents usage of insecure default passwords.')
        }


class UserPermissionsForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = ['is_staff']


class UserProfilePermissionsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['has_api_access']

        help_texts = {
            'has_api_access': _('For service accounts used by the testing module.')
        }

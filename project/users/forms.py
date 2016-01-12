# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import auth
from models import UserFolder, UserProfile
from mptt.forms import TreeNodeChoiceField


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


class CreateUserForm(auth.forms.UserCreationForm):
    pass


class CreateUsersMassForm(forms.Form):
    tsv = forms.CharField(widget=forms.Textarea, required=True,
                          label=_('Data about users'),
                          help_text=_(u'Lines in the format of “[username] [last name] [first name]” or “[username] [last name] [first name] [patronymic]”.'))
    password = forms.CharField(required=True, label=_('Password'))

    def clean_tsv(self):
        data = self.cleaned_data['tsv']
        user_model = auth.get_user_model()
        users = []

        usernames = set()

        for number, line in enumerate(data.split('\n')):
            line = line.strip()
            if not line:
                continue
            tokens = line.split()
            if len(tokens) == 3:
                username, first_name, last_name = tokens
                patronymic = ''
            elif len(tokens) == 4:
                username, first_name, last_name, patronymic = tokens
            else:
                raise forms.ValidationError(_(u'Line %(number)s does not match the template.'),
                                            code='tokens', params={'number': number + 1})

            if username in usernames:
                raise forms.ValidationError(_(u'User “%(username)s” is listed more than once.'),
                                            code='duplicate', params={'username': username})
            usernames.add(username)

            user = user_model(username=username, first_name=first_name, last_name=last_name)
            userprofile = UserProfile(patronymic=patronymic, needs_change_password=True, folder=None)
            users.append((user, userprofile))

        return users

    def clean(self):
        super(CreateUsersMassForm, self).clean()
        password = self.cleaned_data.get('password')
        users = self.cleaned_data.get('tsv')

        if password is not None and users is not None:
            errors = []
            for user, userprofile in users:
                try:
                    user.set_password(password)
                    user.full_clean()

                    userprofile.full_clean(exclude=['user'])
                except forms.ValidationError as e:
                    print e
                    errors.extend(e.messages)
            if errors:
                raise forms.ValidationError(errors)


class MoveUsersForm(forms.Form):
    folder = TreeNodeChoiceField(label=_('Destination folder'), queryset=UserFolder.objects.all(), required=False)

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
        fields = ['is_active', 'email', 'last_name', 'first_name']


class UserProfileForm(forms.ModelForm):
    folder = TreeNodeChoiceField(label=_('Folder'), queryset=UserFolder.objects.all(), required=False)

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

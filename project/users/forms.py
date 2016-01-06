# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import auth
from models import UserFolder
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
            users.append(user)

        return users

    def clean(self):
        super(CreateUsersMassForm, self).clean()
        password = self.cleaned_data.get('password')
        users = self.cleaned_data.get('tsv')

        if password is not None and users is not None:
            errors = []
            for user in users:
                try:
                    user.set_password(password)
                    user.full_clean()
                except forms.ValidationError as e:
                    errors.extend(e.messages)
            if errors:
                raise forms.ValidationError(errors)


class MoveUsersForm(forms.Form):
    folder = TreeNodeChoiceField(label=_('Destination folder'), queryset=UserFolder.objects.all(), required=False)

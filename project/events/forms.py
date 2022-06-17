from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _

from common.constants import EMPTY_SELECT
from common.password.gen import get_algo_slugs, get_algo
from common.tree.fields import FolderChoiceField

from storage.fields import FileMetadataField
from tex.fields import TeXTextarea

from cauth.acl.accessmode import AccessMode
from events.models import Event, Page
from users.loader import UserFolderLoader


class PageDesignForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['local_description', 'en_description', 'logo_style', 'logo_file']
        widgets = {
            'local_description': TeXTextarea(),
            'en_description': TeXTextarea(),
        }

    logo_file = FileMetadataField(label=_('Logo image file'), required=False)


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ['slug', 'when', 'is_public', 'local_name', 'en_name', 'local_content', 'en_content']
        widgets = {
            'local_content': TeXTextarea(),
            'en_content': TeXTextarea(),
        }

    def clean(self):
        cleaned_data = super().clean()
        cur_slug = cleaned_data.get('slug')
        if cur_slug is not None and Page.objects.filter(slug=cur_slug, event=self.instance.event).exists():
            msg = _('URL already exists.')
            self.add_error('slug', msg)
        return cleaned_data


def validate_pattern(value):
    if not value:
        return
    try:
        value % (42,)
    except TypeError:
        raise ValidationError(_('Invalid format string'))


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['slug', 'local_name', 'en_name', 'is_registration_available', 'registration_mode', 'fill_forms_in_en',
                  'auto_create_users', 'user_folder', 'username_pattern', 'password_generation_algo', 'contest']
        widgets = {
            'username_pattern': forms.TextInput(attrs={'placeholder': 'fpmi20t%02d', 'class': 'ir-monospace'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        choices = [(None, EMPTY_SELECT)] + [(algo, algo) for algo in get_algo_slugs()]
        examples = [ugettext('Ex.')] + ['<b>{}</b>: {}'.format(algo, ', '.join(get_algo(algo).gen() for _ in range(3))) for algo in get_algo_slugs()]
        self.fields['password_generation_algo'] = forms.ChoiceField(
            label=_('Password generation algorithm'), choices=choices, required=False,
            help_text='<br>'.join(examples)
        )

        self.fields['user_folder'] = FolderChoiceField(
            label=_('Destination folder'), loader_cls=UserFolderLoader, user=user,
            required=False, required_mode=AccessMode.WRITE, none_means_not_set=True
        )

        self.fields['username_pattern'].validators = [validate_pattern]

        self.fields['contest'].empty_label = EMPTY_SELECT

    def clean(self):
        cleaned_data = super().clean()
        auto_create_users = cleaned_data.get('auto_create_users')
        if auto_create_users:
            for field in ['user_folder', 'username_pattern', 'password_generation_algo']:
                if not cleaned_data.get(field):
                    self.add_error(field, _('If the user creation is on, this field is required'))
        return cleaned_data

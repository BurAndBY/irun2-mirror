from django import forms
from django.utils.translation import ugettext_lazy as _

from storage.fields import FileMetadataField
from tex.fields import TeXTextarea

from events.models import Event, Page


class PageDesignForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['local_description', 'en_description', 'logo_style', 'logo_file']

    logo_file = FileMetadataField(label=_('Logo image file'), required=False)


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ['slug', 'when', 'is_public', 'local_name', 'en_name', 'local_content', 'en_content']
        widgets = {
            'local_content': TeXTextarea(),
            'en_content': TeXTextarea(),
        }

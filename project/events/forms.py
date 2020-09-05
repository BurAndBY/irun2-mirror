from django import forms
from django.utils.translation import ugettext_lazy as _

from storage.fields import FileMetadataField

from events.models import Event


class PageDesignForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['local_description', 'en_description', 'logo_style', 'logo_file']

    logo_file = FileMetadataField(label=_('Logo image file'), required=False)

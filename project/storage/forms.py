# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _


class TextOrUploadForm(forms.Form):
    text = forms.CharField(
        label=_('Enter text here'),
        required=False,
        widget=forms.Textarea(),
        max_length=2**20
    )
    upload = forms.FileField(
        label=_('…or upload a file'),
        required=False,
        widget=forms.FileInput,
        max_length=256,
        help_text=_('If you select a file, text field content is ignored.')
    )

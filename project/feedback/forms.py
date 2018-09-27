from django import forms
from django.utils.translation import ugettext_lazy as _

from feedback.models import FeedbackMessage


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = FeedbackMessage
        fields = ['email', 'subject', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5}),
        }


class FeedbackFormWithUpload(FeedbackForm):
    upload = forms.FileField(
        label=_('Attachment'),
        help_text=_('You can attach an arbitrary file to your message'),
        required=False,
        max_length=255
    )

from django import forms

from models import FeedbackMessage


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = FeedbackMessage
        fields = ['email', 'subject', 'body']


class FeedbackFormWithUpload(FeedbackForm):
    upload = forms.FileField(
        label='Attachment',
        required=False,
        max_length=255
    )

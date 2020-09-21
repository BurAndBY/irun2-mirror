from django import forms

from tex.fields import TeXTextarea

from news.models import NewsMessage


class MessageForm(forms.ModelForm):
    class Meta:
        model = NewsMessage
        fields = ['subject', 'body', 'is_public']
        widgets = {
            'body': TeXTextarea()
        }

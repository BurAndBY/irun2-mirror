from django import forms


class TextOrUploadForm(forms.Form):
    text = forms.CharField(
        label='Enter text here',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control'}),
        max_length=2**20
    )
    upload = forms.FileField(
        label='... or upload a file',
        required=False,
        widget=forms.FileInput,
        max_length=256
    )

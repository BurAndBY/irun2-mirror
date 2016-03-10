from django import forms
from django.core.files.base import ContentFile
from django.utils.translation import ugettext_lazy as _

from common.mptt_fields import OrderedTreeNodeMultipleChoiceField

from .models import Problem, ProblemFolder, TestCase, ProblemRelatedFile, ProblemRelatedSourceFile
from .fields import TimeLimitField, MemoryLimitField

'''
Edit single problem
'''


class ProblemForm(forms.ModelForm):
    folders = OrderedTreeNodeMultipleChoiceField(label=_('Problem folder'), queryset=None, required=False)

    class Meta:
        model = Problem
        fields = ['number', 'subnumber', 'full_name', 'short_name', 'difficulty', 'input_filename', 'output_filename', 'folders']

    def __init__(self, *args, **kwargs):
        super(ProblemForm, self).__init__(*args, **kwargs)
        self.fields['folders'].queryset = ProblemFolder.objects.all()


class ProblemExtraInfoForm(forms.ModelForm):
    class Meta:
        fields = ['offered', 'description', 'hint']


class TestDescriptionForm(forms.ModelForm):
    time_limit = TimeLimitField(required=True)
    memory_limit = MemoryLimitField(required=False)

    class Meta:
        model = TestCase
        fields = ['description', 'points', 'time_limit', 'memory_limit']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class TestUploadOrTextForm(forms.Form):
    upload = forms.FileField(required=False, widget=forms.FileInput)
    text = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'ir-monospace'}))

    def extract_file_result(self):
        '''
        Always returns not None.
        '''
        upload = self.cleaned_data['upload']
        if upload is None:
            text = self.cleaned_data['text']
            upload = ContentFile(text.encode('utf-8'))
        return upload


class TestUploadForm(forms.Form):
    upload = forms.FileField(required=False, widget=forms.FileInput)

    def __init__(self, *args, **kwargs):
        representation = kwargs.pop('representation')
        super(TestUploadForm, self).__init__(*args, **kwargs)
        self.representation = representation

    def extract_file_result(self):
        upload = self.cleaned_data['upload']
        return upload


class MassSetTimeLimitForm(forms.Form):
    time_limit = TimeLimitField(label=_('Time limit'), required=True)


class MassSetMemoryLimitForm(forms.Form):
    memory_limit = MemoryLimitField(label=_('Memory limit'), required=False)


class ProblemRelatedDataFileForm(forms.ModelForm):
    upload = forms.FileField(label=_('File'), required=False, widget=forms.FileInput)

    class Meta:
        model = ProblemRelatedFile
        fields = ['file_type', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }


class ProblemRelatedSourceFileForm(forms.ModelForm):
    upload = forms.FileField(label=_('File'), required=False, widget=forms.FileInput)

    class Meta:
        model = ProblemRelatedSourceFile
        fields = ['file_type', 'compiler', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

'''
Problem search
'''


class ProblemSearchForm(forms.Form):
    query = forms.CharField(required=False)


'''
TeX
'''


class TeXForm(forms.Form):
    source = forms.CharField(required=False, max_length=32768, widget=forms.Textarea(attrs={'class': 'ir-monospace', 'rows': 20, 'autofocus': 'autofocus'}))


class ProblemRelatedTeXFileForm(forms.ModelForm):
    class Meta:
        model = ProblemRelatedFile
        fields = ['filename']

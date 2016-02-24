from django import forms
from .models import Problem, ProblemFolder, TestCase, ProblemRelatedFile, ProblemRelatedSourceFile
from common.mptt_fields import OrderedTreeNodeMultipleChoiceField
from django.utils.translation import ugettext_lazy as _

'''
Edit single problem
'''


class ProblemForm(forms.ModelForm):
    folders = OrderedTreeNodeMultipleChoiceField(label=_('Problem folder'), queryset=ProblemFolder.objects.all(), required=False)

    class Meta:
        model = Problem
        fields = ['number', 'subnumber', 'full_name', 'short_name', 'difficulty', 'input_filename', 'output_filename', 'folders']


class ProblemExtraInfoForm(forms.ModelForm):
    class Meta:
        fields = ['offered', 'description', 'hint']


class TestDescriptionForm(forms.ModelForm):
    class Meta:
        model = TestCase
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }


class TestUploadOrTextForm(forms.Form):
    upload = forms.FileField(required=False, widget=forms.FileInput)
    text = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'ir-monospace'}))


class TestUploadForm(forms.Form):
    upload = forms.FileField(required=False, widget=forms.FileInput)

    def __init__(self, *args, **kwargs):
        representation = kwargs.pop('representation')
        super(TestUploadForm, self).__init__(*args, **kwargs)
        self.representation = representation


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

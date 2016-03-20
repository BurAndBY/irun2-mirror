import zipfile

from django import forms
from django.core.files.base import ContentFile
from django.utils.translation import ugettext_lazy as _

from common.mptt_fields import OrderedTreeNodeMultipleChoiceField

from .importing import extract_tests
from .models import Problem, ProblemFolder, TestCase, ProblemRelatedFile, ProblemRelatedSourceFile
from .fields import TimeLimitField, MemoryLimitField

'''
Edit single problem
'''


class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ['number', 'subnumber', 'full_name', 'short_name', 'difficulty', 'input_filename', 'output_filename']
        help_texts = {
            'input_filename': _('Leave empty to use standard input.'),
            'output_filename': _('Leave empty to use standard output.'),
        }


class ProblemFoldersForm(forms.ModelForm):
    folders = OrderedTreeNodeMultipleChoiceField(
        widget=forms.SelectMultiple(attrs={'size': 20}),
        label=_('Problem folders'),
        queryset=None,
        required=False)

    class Meta:
        model = Problem
        fields = ['folders']

    def __init__(self, *args, **kwargs):
        super(ProblemFoldersForm, self).__init__(*args, **kwargs)
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
        fields = ['filename', 'file_type', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }


class ProblemRelatedSourceFileForm(forms.ModelForm):
    upload = forms.FileField(label=_('File'), required=False, widget=forms.FileInput)

    class Meta:
        model = ProblemRelatedSourceFile
        fields = ['filename', 'file_type', 'compiler', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }


class ProblemTestArchiveUploadForm(forms.Form):
    ARCHIVE_SCHEME_CHOICES = (
        ('/a', u'X / X.a'),
        ('in/out', u'X.in / X.out'),
    )

    upload = forms.FileField(label=_('ZIP-archive'), required=True, widget=forms.FileInput,
                             help_text=_('The archive should not contain any other files except test inputs and outputs.'))
    scheme = forms.ChoiceField(label=_('File naming scheme'), required=True, choices=ARCHIVE_SCHEME_CHOICES)
    time_limit = TimeLimitField(label=_('Time limit'), required=True)
    memory_limit = MemoryLimitField(label=_('Memory limit'), required=False)

    def clean(self):
        cleaned_data = super(ProblemTestArchiveUploadForm, self).clean()
        upload = cleaned_data.get('upload')
        scheme = cleaned_data.get('scheme')

        if upload is not None and scheme is not None:
            filenames = []
            try:
                with zipfile.ZipFile(upload, 'r', allowZip64=True) as myzip:
                    # Consider only root directory. Zip always uses forward slashes.
                    filenames = [filename for filename in myzip.namelist() if '/' not in filename]
            except zipfile.BadZipfile:
                self.add_error('upload', _('Archive format is not supported.'))
                return

            if scheme == '/a':
                tests = extract_tests(filenames, None, 'a')
            elif scheme == 'in/out':
                tests = extract_tests(filenames, 'in', 'out')
            else:
                tests = []

            if len(tests) == 0:
                raise forms.ValidationError(_('No test files found in the archive.'), code='empty')

            cleaned_data['tests'] = tests


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

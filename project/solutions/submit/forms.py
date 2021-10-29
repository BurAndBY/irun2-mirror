# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import ugettext_lazy as _

from common.constants import EMPTY_SELECT
from proglangs.langlist import (
    split_language_codes,
    get_language_label,
)
from proglangs.models import Compiler
from proglangs.utils import guess_filename
from storage.validators import validate_filename
from problems.models import Problem, ProblemExtraInfo

from solutions.submit.limit import UnlimitedPolicy


class SolutionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self._limit_policy = kwargs.pop('limit_policy', UnlimitedPolicy())
        super().__init__(*args, **kwargs)

    compiler = forms.ModelChoiceField(
        label=_('Compiler'),
        required=True,
        queryset=Compiler.objects.all().order_by('description'),
        empty_label=EMPTY_SELECT,
    )
    text = forms.CharField(
        label=_('Enter source code'),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control ir-monospace', 'rows': 8}),
        max_length=2**20
    )
    upload = forms.FileField(
        label=_('…or upload a file'),
        required=False,
        widget=forms.FileInput,
        max_length=255,
        help_text=_('If you select a file, text field content is ignored.')
    )

    def _check_size(self, text, upload):
        file_size_limit = self._limit_policy.file_size_limit
        if file_size_limit is None:
            return

        size = 0
        if upload is not None:
            size = upload.size
        elif text is not None:
            size = len(text.encode('utf-8'))

        if size > file_size_limit:
            raise forms.ValidationError(
                _('The size of the source file (%(actual)d B) exceeds the limit (%(limit)d B).'),
                code='too_big',
                params={'actual': size, 'limit': file_size_limit},
            )

    def _check_attempts(self, problem_id):
        if not self._limit_policy.can_submit(problem_id):
            raise forms.ValidationError(_('Attempt count limit is reached.'), code='limit')

    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get('text')
        upload = cleaned_data.get('upload')
        compiler = cleaned_data.get('compiler')
        problem_id = cleaned_data.get('problem')

        if (upload is None) and (text is not None) and (len(text) == 0):
            raise forms.ValidationError(_('Unable to submit an empty solution.'), code='empty')

        filename = None
        if upload is not None:
            filename = upload.name
        else:
            # need to guess filename
            if compiler is not None and text is not None:
                filename = guess_filename(compiler.language, text)

        if filename is None:
            raise forms.ValidationError(_('Unable to determine the name of the source file. '
                                          'For Java code, make sure you have a single public class defined. '
                                          'You can also try to upload a file instead of using direct input of code.'), code='no_name')

        validate_filename(filename)
        cleaned_data['filename'] = filename

        self._check_size(text, upload)
        self._check_attempts(problem_id)
        return cleaned_data


class ProblemSolutionForm(SolutionForm):
    '''
    Allows to choose a problem.
    '''

    problem = forms.TypedChoiceField(
        label=_('Problem'),
        choices=Problem.objects.none(),
        coerce=int
    )

    def clean(self):
        cleaned_data = super().clean()

        problem = cleaned_data.get('problem')
        if problem is not None:
            compiler = cleaned_data.get('compiler')
            if compiler is not None:
                allowed_languages = ProblemExtraInfo.objects.filter(problem=problem).\
                    values_list('allowed_programming_languages', flat=True).first()
                if allowed_languages:
                    codes = list(split_language_codes(allowed_languages))
                    if compiler.language not in codes:
                        err = forms.ValidationError(_('This problem must be solved in %(langs)s'),
                                                    params={'langs': ', '.join(get_language_label(code) for code in codes)},
                                                    code='language_restriction')
                        self.add_error('compiler', err)

        return cleaned_data

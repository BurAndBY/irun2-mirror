# -*- coding: utf-8 -*-

import re

from collections import OrderedDict

from django import forms
from django.utils.translation import ugettext_lazy as _

from common.constants import EMPTY_SELECT
from problems.fields import ThreePanelGenericProblemMultipleChoiceField
from solutions.forms import SolutionForm
from users.fields import ThreePanelUserMultipleChoiceField

from contests.printing import check_size_limits
from contests.models import Contest, Message, Printout, UserFilter


class PropertiesForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['name', 'rules', 'kind', 'start_time', 'duration', 'freeze_time', 'show_pending_runs', 'unfreeze_standings', 'enable_upsolving']


class AccessForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['unauthorized_access', 'contestant_own_solutions_access']
        help_texts = {
            'contestant_own_solutions_access': _('Each access level includes all the previous onces.')
        }


class LimitsForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['attempt_limit', 'file_size_limit']


class CompilersForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['compilers']
        labels = {
            'compilers': ''
        }
        widgets = {
            'compilers': forms.CheckboxSelectMultiple
        }


class PrintingForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['enable_printing', 'rooms']


class ThreePanelProblemMultipleChoiceField(ThreePanelGenericProblemMultipleChoiceField):
    @classmethod
    def label_from_instance(cls, obj):
        return obj.numbered_full_name()


class ProblemsForm(forms.Form):
    problems = ThreePanelProblemMultipleChoiceField(label=_('Problems'), required=False,
                                                    help_text=_('Order of problem addition is significant.'))


class StatementsForm(forms.Form):
    upload = forms.FileField(label=_('Statements file'), required=False,
                             help_text=_('You can upload a single file containing statements of all problems (usually in PDF format).'))


class UsersForm(forms.Form):
    users = ThreePanelUserMultipleChoiceField(label=_('Users'), required=False)


class SolutionListUserForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user_choices = kwargs.pop('user_choices')
        super(SolutionListUserForm, self).__init__(*args, **kwargs)
        self.fields['user'] = forms.TypedChoiceField(label=_('User'), choices=user_choices, coerce=int, empty_value=None, required=False)
        self.fields['user'].widget.attrs['class'] = 'form-control'


class SolutionListProblemForm(forms.Form):
    def __init__(self, *args, **kwargs):
        problem_choices = kwargs.pop('problem_choices')
        super(SolutionListProblemForm, self).__init__(**kwargs)
        self.fields['problem'] = forms.TypedChoiceField(label=_('Problem'), choices=problem_choices, coerce=int, empty_value=None, required=False)
        self.fields['problem'].widget.attrs['class'] = 'form-control'


class ContestSolutionForm(SolutionForm):
    def __init__(self, problem_choices, compiler_queryset, **kwargs):
        super(ContestSolutionForm, self).__init__(**kwargs)
        self.fields['problem'] = forms.TypedChoiceField(label=_('Problem'), choices=problem_choices, coerce=int)
        self.fields['compiler'].queryset = compiler_queryset


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'text']

    def __init__(self, *args, **kwargs):
        recipient_id_choices = kwargs.pop('recipient_id_choices', None)
        super(MessageForm, self).__init__(*args, **kwargs)

        if recipient_id_choices is not None:
            # reorder fields
            new_fields = OrderedDict()
            new_fields['recipient_id'] = forms.TypedChoiceField(label=_('To'), choices=recipient_id_choices, required=False, coerce=int)
            new_fields['subject'] = self.fields['subject']
            new_fields['text'] = self.fields['text']
            self.fields = new_fields


class AnswerForm(forms.ModelForm):
    answers = forms.IntegerField(required=True, widget=forms.HiddenInput)

    class Meta:
        model = Message
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'text']

    def __init__(self, *args, **kwargs):
        problem_id_choices = kwargs.pop('problem_id_choices', None)
        super(QuestionForm, self).__init__(*args, **kwargs)

        if problem_id_choices is not None:
            # reorder fields
            new_fields = OrderedDict()
            new_fields['problem_id'] = forms.TypedChoiceField(label=_('Problem'), choices=problem_id_choices, required=False, coerce=int)
            new_fields['subject'] = self.fields['subject']
            new_fields['text'] = self.fields['text']
            self.fields = new_fields


def _make_room_choices(rooms_str):
    rooms = [x for x in (x.strip() for x in rooms_str.split(',')) if x]
    return [(None, EMPTY_SELECT)] + [(x, x) for x in rooms]


class PrintoutForm(forms.ModelForm):
    class Meta:
        model = Printout
        fields = ['room', 'text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control ir-monospace', 'rows': 12}),
            'room': forms.Select(),
        }
        help_texts = {
            'room': _('Choose the room where you are to use the closest printer.')
        }

    def __init__(self, *args, **kwargs):
        rooms = kwargs.pop('rooms')
        super(PrintoutForm, self).__init__(*args, **kwargs)
        self.fields['room'].widget.choices = _make_room_choices(rooms)

    def clean_text(self):
        text = self.cleaned_data.get('text')

        if (text is not None) and (not check_size_limits(text)):
            raise forms.ValidationError(_('Text is too long.'), code='length')

        return text


class EditPrintoutForm(forms.ModelForm):
    class Meta:
        model = Printout
        fields = ['room', 'status']


class UserFilterForm(forms.ModelForm):
    class Meta:
        model = UserFilter
        fields = ['name', 'regex']

    def clean_regex(self):
        data = self.cleaned_data['regex']
        try:
            re.compile(data)
        except re.error:
            raise forms.ValidationError('Invalid regular expression.')
        return data

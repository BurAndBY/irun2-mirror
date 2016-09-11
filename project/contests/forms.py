# -*- coding: utf-8 -*-

from collections import OrderedDict

from django import forms
from django.contrib import auth
from django.utils.translation import ugettext_lazy as _

from common.fields import TwoPanelModelMultipleChoiceField
from problems.models import Problem, ProblemFolder
from solutions.forms import SolutionForm
from users.models import UserFolder

from .models import Contest, Message


class PropertiesForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['name', 'rules', 'start_time', 'duration', 'freeze_time', 'show_pending_runs', 'unfreeze_standings', 'enable_upsolving',
                  'unauthorized_access', 'contestant_own_solutions_access', 'attempt_limit', 'file_size_limit']
        help_texts = {
            'contestant_own_solutions_access': _('Each access level includes all the previous onces.')
        }
        widgets = {
            'rules': forms.Select(attrs={'disabled': True}),
        }


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


class TwoPanelProblemMultipleChoiceField(TwoPanelModelMultipleChoiceField):
    @classmethod
    def label_from_instance(cls, obj):
        return obj.numbered_full_name()


class ProblemsForm(forms.Form):
    problems = TwoPanelProblemMultipleChoiceField(label=_('Problems'), required=False,
                                                  help_text=_('Order of problem addition is significant.'),
                                                  model=Problem, folder_model=ProblemFolder, clean_to_list=True,
                                                  url_pattern='contests:settings_problems_json_list')


class StatementsForm(forms.Form):
    upload = forms.FileField(label=_('Statements file'), required=False,
                             help_text=_('You can upload a single file containing statements of all problems (usually in PDF format).'))


class TwoPanelUserMultipleChoiceField(TwoPanelModelMultipleChoiceField):
    @classmethod
    def label_from_instance(cls, obj):
        return obj.get_full_name()


class UsersForm(forms.Form):
    users = TwoPanelUserMultipleChoiceField(label=_('Users'), required=False,
                                            model=auth.get_user_model(), folder_model=UserFolder,
                                            url_pattern='contests:settings_users_json_list')


class SolutionListUserForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user_choices = kwargs.pop('user_choices')
        super(SolutionListUserForm, self).__init__(*args, **kwargs)
        self.fields['user'] = forms.TypedChoiceField(label=_('User'), choices=user_choices, coerce=int, empty_value=None, required=True)
        self.fields['user'].widget.attrs['class'] = 'form-control'


class SolutionListProblemForm(forms.Form):
    def __init__(self, *args, **kwargs):
        problem_choices = kwargs.pop('problem_choices')
        super(SolutionListProblemForm, self).__init__(**kwargs)
        self.fields['problem'] = forms.TypedChoiceField(label=_('Problem'), choices=problem_choices, coerce=int, empty_value=None, required=True)
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

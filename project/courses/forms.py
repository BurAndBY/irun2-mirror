# -*- coding: utf-8 -*-

from django import forms
from django.contrib import auth
from django.utils.translation import ugettext_lazy as _

from problems.models import Problem, ProblemFolder
from users.models import UserFolder
from common.constants import EMPTY_SELECT
from common.fields import TwoPanelModelMultipleChoiceField
from common.mptt_fields import OrderedTreeNodeChoiceField
import common.widgets
import solutions.forms

from .models import Topic, Course, Activity, Assignment, ActivityRecord, Subgroup, Membership, MailThread, MailMessage


class PropertiesForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'student_own_solutions_access', 'student_all_solutions_access', 'enable_sheet', 'attempts_a_day']
        help_texts = {
            'student_own_solutions_access': _('Each access level includes all the previous onces.')
        }


class CompilersForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['compilers']
        labels = {
            'compilers': ''
        }
        widgets = {
            'compilers': forms.CheckboxSelectMultiple
        }


class TopicForm(forms.ModelForm):
    problem_folder = OrderedTreeNodeChoiceField(label=_('Problem folder'), queryset=None)
    num_problems = forms.IntegerField(label=_('Problems to assign per student in the course'), min_value=0, max_value=10, initial=1)

    class Meta:
        model = Topic
        fields = ['name', 'problem_folder', 'criteria']
        widgets = {
            'criteria': forms.CheckboxSelectMultiple
        }

    def __init__(self, *args, **kwargs):
        super(TopicForm, self).__init__(*args, **kwargs)
        self.fields['problem_folder'].queryset = ProblemFolder.objects.order_by('name')


class ActivityForm(forms.ModelForm):
    weight = forms.FloatField(label=_('Weight coefficient'), max_value=1.0, min_value=0.0, initial=0.0,
                              widget=forms.NumberInput(attrs={'step': 0.01}))

    class Meta:
        model = Activity
        fields = ['name', 'description', 'kind', 'weight']


class SubgroupForm(forms.ModelForm):
    class Meta:
        model = Subgroup
        fields = ['name']
        help_texts = {
            'name': _(u'Use short subgroup names, e. g. &laquo;1st&raquo;, &laquo;2 s.&raquo;, &laquo;EPS&raquo;.')
        }


class ProblemModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.numbered_full_name()


class ProblemAssignmentForm(forms.ModelForm):
    problem = ProblemModelChoiceField(label=_('Problem'), queryset=None, required=False,
                                      widget=common.widgets.SelectWithGrayOut(attrs={'class': 'form-control ir-choose-problem'}))

    class Meta:
        model = Assignment
        fields = ['problem', 'criteria', 'extra_requirements', 'extra_requirements_ok']
        widgets = {
            'criteria': forms.CheckboxSelectMultiple,
            'extra_requirements': forms.Textarea(attrs={'rows': 2}),
        }


class AddExtraProblemSlotForm(forms.Form):
    penaltytopic = forms.ModelChoiceField(label=_('Topic'), queryset=None, empty_label=EMPTY_SELECT)


class TwoPanelUserMultipleChoiceField(TwoPanelModelMultipleChoiceField):
    @classmethod
    def label_from_instance(cls, obj):
        return obj.get_full_name()


class CourseUsersForm(forms.Form):
    users = TwoPanelUserMultipleChoiceField(label=_('Users'), required=False,
                                            model=auth.get_user_model(), folder_model=UserFolder,
                                            url_pattern='courses:course_settings_users_json_list')


class TwoPanelProblemMultipleChoiceField(TwoPanelModelMultipleChoiceField):
    @classmethod
    def label_from_instance(cls, obj):
        return obj.numbered_full_name_difficulty()


class CourseCommonProblemsForm(forms.ModelForm):
    common_problems = TwoPanelProblemMultipleChoiceField(label=_('Problems'), required=False,
                                                         model=Problem, folder_model=ProblemFolder,
                                                         url_pattern='courses:course_settings_problems_json_list')

    class Meta:
        model = Course
        fields = ['common_problems']


class SolutionForm(solutions.forms.SolutionForm):
    def __init__(self, problem_choices, compiler_queryset, attempt_limit_checker, **kwargs):
        super(SolutionForm, self).__init__(**kwargs)
        self.fields['problem'] = forms.TypedChoiceField(label=_('Problem'), choices=problem_choices, coerce=int)
        self.fields['compiler'].queryset = compiler_queryset
        self.attempt_limit_checker = attempt_limit_checker

    def clean(self):
        cleaned_data = super(SolutionForm, self).clean()
        problem = cleaned_data.get('problem')
        if problem is not None:
            if self.attempt_limit_checker(problem):
                raise forms.ValidationError(_('Attempt count limit is reached.'), code='limit')
        return cleaned_data


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


class ActivityRecordFakeForm(forms.Form):
    mark = forms.IntegerField(required=False)
    enum = forms.TypedChoiceField(required=False, empty_value=None, choices=ActivityRecord.CHOICES, coerce=int)


def create_member_subgroup_form_class(subgroups):
    '''
    Subgroups are different for different courses, so we define the form class dynamically.

    args:
        subgroups: queryset of Subgroup objects
    '''

    # hacks saves us from queryset evaluation for each user
    choices = [('', _('no'))]
    for subgroup in subgroups:
        choices.append((str(subgroup.id), subgroup.name))

    class MemberSubgroupForm(forms.ModelForm):
        subgroup = forms.ModelChoiceField(queryset=subgroups, widget=forms.RadioSelect, required=False)

        def __init__(self, *args, **kwargs):
            super(MemberSubgroupForm, self).__init__(*args, **kwargs)
            self.fields['subgroup'].choices = choices

        class Meta:
            model = Membership
            fields = ['subgroup']

    return MemberSubgroupForm


def create_member_subgroup_formset_class(subgroups):
    form = create_member_subgroup_form_class(subgroups)
    return forms.modelformset_factory(Membership, form=form)


'''
Messaging
'''


class MailThreadForm(forms.ModelForm):
    class Meta:
        model = MailThread
        fields = ['subject']

    def __init__(self, *args, **kwargs):
        problem_choices = kwargs.pop('problem_choices', None)
        person_choices = kwargs.pop('person_choices', None)

        super(MailThreadForm, self).__init__(*args, **kwargs)

        if problem_choices is not None:
            self.fields['problem'] = forms.TypedChoiceField(label=_('Problem'), choices=problem_choices, required=False, coerce=int)
        if person_choices is not None:
            self.fields['person'] = forms.TypedChoiceField(label=_('Student'), choices=person_choices, required=False, coerce=int)


class MailMessageForm(forms.ModelForm):
    upload = forms.FileField(
        label=_('Attachment'),
        help_text=_('You can attach an arbitrary file to your message'),
        required=False,
        max_length=255
    )

    class Meta:
        model = MailMessage
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5}),
        }


class MailResolvedForm(forms.Form):
    resolved = forms.BooleanField(required=False)

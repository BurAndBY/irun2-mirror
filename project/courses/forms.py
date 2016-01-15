# -*- coding: utf-8 -*-

from django import forms
from .models import Topic, Course, Activity, Assignment, ActivityRecord, Subgroup, Membership
from problems.models import Problem, ProblemFolder
from users.models import UserFolder
from proglangs.models import Compiler
from mptt.forms import TreeNodeChoiceField
from django.utils.translation import ugettext_lazy as _
from common.constants import EMPTY_SELECT
import common.widgets
import common.fields
from django.contrib import auth
import solutions.forms


class PropertiesForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'student_own_solutions_access', 'student_all_solutions_access', 'enable_sheet']
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
    problem_folder = TreeNodeChoiceField(label=_('Problem folder'), queryset=ProblemFolder.objects.all())
    num_problems = forms.IntegerField(label=_('Problems to assign per student in the course'), min_value=0, max_value=10, initial=1)

    class Meta:
        model = Topic
        fields = ['name', 'problem_folder', 'criteria']
        widgets = {
            'criteria': forms.CheckboxSelectMultiple
        }


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
    penaltytopic = forms.ModelChoiceField(label=_('Topic:'), queryset=None)


class TwoPanelUserMultipleChoiceField(common.fields.TwoPanelModelMultipleChoiceField):
    @classmethod
    def label_from_instance(cls, obj):
        return obj.get_full_name()


class CourseUsersForm(forms.Form):
    users = TwoPanelUserMultipleChoiceField(label=_('Users'), required=False,
                                            model=auth.get_user_model(), folder_model=UserFolder,
                                            url_pattern='courses:course_settings_users_json_list')


class SolutionForm(solutions.forms.SolutionForm):
    def __init__(self, problem_choices, compiler_queryset, **kwargs):
        super(SolutionForm, self).__init__(**kwargs)
        self.fields['problem'] = forms.TypedChoiceField(label=_('Problem'), choices=problem_choices, coerce=int)
        self.fields['compiler'].queryset = compiler_queryset


class SolutionListMemberForm(forms.Form):
    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('queryset')
        super(SolutionListMemberForm, self).__init__(*args, **kwargs)
        self.fields['membership'] = forms.ModelChoiceField(label=_('User'), empty_label=EMPTY_SELECT, queryset=queryset, required=False)
        self.fields['membership'].widget.attrs['class'] = 'form-control'


class SolutionListProblemForm(forms.Form):
    def __init__(self, problem_choices, **kwargs):
        super(SolutionListProblemForm, self).__init__(**kwargs)
        self.fields['problem'] = forms.TypedChoiceField(label=_('Problem'), choices=problem_choices, coerce=int, empty_value=None, required=False)
        self.fields['problem'].widget.attrs['class'] = 'form-control'


class ActivityRecordFakeForm(forms.Form):
    mark = forms.IntegerField(required=False)
    enum = forms.TypedChoiceField(required=False, empty_value=None, choices=ActivityRecord.CHOICES, coerce=int)


def create_member_subgroup_form_class(course):
    '''
    Subgroups are different for different courses, so we define the form class dynamically.
    '''
    queryset = course.subgroup_set.all().order_by('id')

    class MemberSubgroupForm(forms.ModelForm):
        subgroup = forms.ModelChoiceField(queryset=queryset, widget=forms.RadioSelect, empty_label=_('no'), required=False)

        class Meta:
            model = Membership
            fields = ['subgroup']

    return MemberSubgroupForm


def create_member_subgroup_formset_class(course):
    form = create_member_subgroup_form_class(course)
    return forms.modelformset_factory(Membership, form=form)

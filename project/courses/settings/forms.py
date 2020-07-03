# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.contrib import auth
from django.utils.translation import ugettext_lazy as _

from problems.fields import ThreePanelGenericProblemMultipleChoiceField
from problems.models import Problem, ProblemFolder
from quizzes.models import QuizInstance
from users.models import UserFolder
from common.constants import EMPTY_SELECT
from common.tree.fields import TwoPanelModelMultipleChoiceField
from common.tree.mptt_fields import OrderedTreeNodeChoiceField

from courses.models import (
    Activity,
    Course,
    Membership,
    Queue,
    Subgroup,
    Topic,
)
from courses.forms import (
    make_year_of_study_choices,
    make_academic_year_choices,
)


class PropertiesForm(forms.ModelForm):
    year_of_study = forms.TypedChoiceField(label=_('Year of study'), required=False,
                                           choices=make_year_of_study_choices, coerce=int, empty_value=None)
    academic_year = forms.TypedChoiceField(label=_('Academic year'), required=False,
                                           choices=make_academic_year_choices, coerce=int, empty_value=None)

    class Meta:
        model = Course
        fields = ['name', 'year_of_study', 'group', 'academic_year', 'status', 'enable_sheet', 'enable_queues', 'attempts_a_day']


class AccessForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['student_own_solutions_access', 'student_all_solutions_access', 'teacher_all_solutions_access', 'owner']
        help_texts = {
            'student_own_solutions_access': _('Each access level includes all the previous onces.')
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['owner'].user = user


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
    num_problems = forms.IntegerField(label=_('Problems to assign per student in the course'),
                                      min_value=0, max_value=10, initial=1)

    class Meta:
        model = Topic
        fields = ['name', 'problem_folder', 'criteria', 'deadline']
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
        fields = ['name', 'description', 'kind', 'quiz_instance', 'weight']

    def __init__(self, *args, **kwargs):
        course_id = kwargs.pop('course_id', None)
        super(ActivityForm, self).__init__(*args, **kwargs)
        if course_id:
            self.fields['quiz_instance'].queryset = QuizInstance.objects.filter(course_id=course_id)


class SubgroupForm(forms.ModelForm):
    class Meta:
        model = Subgroup
        fields = ['name']
        help_texts = {
            'name': _('Use short subgroup names, e. g. ‘1st’, ‘2 s.’, ‘EPS’.')
        }


class QuizInstanceCreateForm(forms.ModelForm):
    class Meta:
        model = QuizInstance
        fields = ['quiz_template']


class QuizInstanceUpdateForm(forms.ModelForm):
    class Meta:
        model = QuizInstance
        fields = ['tag', 'attempts', 'time_limit', 'deadline', 'disable_time_limit', 'show_answers', 'enable_discussion']


class TwoPanelUserMultipleChoiceField(TwoPanelModelMultipleChoiceField):
    @classmethod
    def label_from_instance(cls, obj):
        return obj.get_full_name()


class CourseUsersForm(forms.Form):
    users = TwoPanelUserMultipleChoiceField(label=_('Users'), required=False,
                                            model=auth.get_user_model(), folder_model=UserFolder,
                                            url_pattern='courses:settings:users_json_list')


class TwoPanelProblemMultipleChoiceField(TwoPanelModelMultipleChoiceField):
    @classmethod
    def label_from_instance(cls, obj):
        return obj.numbered_full_name_difficulty()


class ThreePanelProblemMultipleChoiceField(ThreePanelGenericProblemMultipleChoiceField):
    @classmethod
    def label_from_instance(cls, obj):
        return obj.numbered_full_name_difficulty()


class CourseCommonProblemsForm(forms.Form):
    common_problems = ThreePanelProblemMultipleChoiceField(label=_('Problems'), required=False,
                                                           help_text=_('Order of problem addition is significant.'))


class TopicCommonProblemsForm(forms.Form):
    common_problems = TwoPanelProblemMultipleChoiceField(label=_('Problems'), required=False,
                                                         model=Problem, folder_model=ProblemFolder,
                                                         clean_to_list=True,
                                                         url_pattern='courses:settings:problems_json_list')


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
Queues
'''


class QueueForm(forms.ModelForm):
    class Meta:
        model = Queue
        fields = ['is_active', 'name', 'subgroup']
        help_texts = {
            'is_active': _('Students may join the queue.')
        }

    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course')
        super(QueueForm, self).__init__(*args, **kwargs)
        self.fields['subgroup'] = forms.ModelChoiceField(
            label=_('Subgroup'),
            queryset=Subgroup.objects.filter(course=course),
            empty_label=EMPTY_SELECT,
            required=False
        )


class QuizMarkFakeForm(forms.Form):
    value = forms.FloatField(required=True, localize=True)
    pk = forms.IntegerField(required=True)

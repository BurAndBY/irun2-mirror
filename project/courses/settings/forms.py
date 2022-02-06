# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from cauth.acl.accessmode import AccessMode
from problems.fields import ThreePanelGenericProblemMultipleChoiceField
from problems.loader import ProblemFolderLoader
from quizzes.models import QuizInstance
from users.fields import ThreePanelUserMultipleChoiceField

from common.constants import EMPTY_SELECT
from common.tree.fields import FolderChoiceField

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
        fields = ['name', 'year_of_study', 'group', 'academic_year', 'status', 'enable_sheet', 'enable_queues', 'attempts_a_day', 'stop_on_fail']


class AccessForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['student_own_solutions_access', 'student_all_solutions_access', 'teacher_all_solutions_access', 'private_mode', 'owner']
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
    problem_folder = FolderChoiceField(label=_('Problem folder'), loader_cls=ProblemFolderLoader,
                                       required=False, required_mode=AccessMode.READ, none_means_not_set=True)
    num_problems = forms.IntegerField(label=_('Problems to assign per student in the course'),
                                      min_value=0, max_value=10, initial=1)

    class Meta:
        model = Topic
        fields = ['name', 'problem_folder', 'criteria', 'deadline', 'overdue_factor']
        widgets = {
            'criteria': forms.CheckboxSelectMultiple
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['problem_folder'].user = user


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


class CourseUsersForm(forms.Form):
    users = ThreePanelUserMultipleChoiceField(label=_('Users'), required=False)


class ThreePanelProblemMultipleChoiceField(ThreePanelGenericProblemMultipleChoiceField):
    @classmethod
    def label_from_instance(cls, obj):
        return obj.numbered_full_name_difficulty()


class CourseCommonProblemsForm(forms.Form):
    common_problems = ThreePanelProblemMultipleChoiceField(label=_('Problems'), required=False,
                                                           help_text=_('Order of problem addition is significant.'))


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


class CloneCourseForm(forms.Form):
    copy_problems = forms.BooleanField(label=_('Problems'), required=False)
    copy_subgroups = forms.BooleanField(label=_('Subgroups'), required=False)
    copy_users = forms.BooleanField(label=_('Users'), required=False)
    copy_queues = forms.BooleanField(label=_('Queues'), required=False)
    copy_quizzes = forms.BooleanField(label=_('Quizzes'), required=False)
    copy_sheet = forms.BooleanField(label=_('Sheet'), required=False)

# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import six

from django import forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from common.constants import EMPTY_SELECT
from common.education.year import (
    make_year_of_study_string, make_academic_year_string
)
import solutions.submit.forms

from courses.models import (
    ActivityRecord,
    Course,
    MailMessage,
    MailThread,
    QueueEntry,
)
from problems.models import (
    ProblemExtraInfo,
)
from proglangs.langlist import (
    split_language_codes,
    get_language_label,
)


def make_year_of_study_choices():
    return [('', '')] + [
        (year, make_year_of_study_string(year))
        for year in six.moves.range(1, 7)
    ]


def make_academic_year_choices():
    cur_year = timezone.now().date().year

    return [('', '')] + [
        (year, make_academic_year_string(year))
        for year in six.moves.range(2004, cur_year + 2)
    ]


class NewCourseForm(forms.ModelForm):
    year_of_study = forms.TypedChoiceField(label=_('Year of study'), required=False,
                                           choices=make_year_of_study_choices, coerce=int, empty_value=None)
    academic_year = forms.TypedChoiceField(label=_('Academic year'), required=False,
                                           choices=make_academic_year_choices, coerce=int, empty_value=None)

    class Meta:
        model = Course
        fields = ['name', 'year_of_study', 'group', 'academic_year', 'owner']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['owner'].user = user


class ProblemModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.numbered_full_name()


class AddExtraProblemSlotForm(forms.Form):
    penaltytopic = forms.ModelChoiceField(label=_('Topic'), queryset=None, empty_label=EMPTY_SELECT)


class SolutionForm(solutions.submit.forms.ProblemSolutionForm):
    def __init__(self, problem_choices, compiler_queryset, *args, **kwargs):
        super(SolutionForm, self).__init__(*args, **kwargs)
        self.fields['problem'].choices = problem_choices
        self.fields['compiler'].queryset = compiler_queryset


class SolutionListUserForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user_choices = kwargs.pop('user_choices')
        super(SolutionListUserForm, self).__init__(*args, **kwargs)
        self.fields['user'] = forms.TypedChoiceField(label=_('User'), choices=user_choices,
                                                     coerce=int, empty_value=None, required=False)
        self.fields['user'].widget.attrs['class'] = 'form-control'


class SolutionListProblemForm(forms.Form):
    def __init__(self, *args, **kwargs):
        problem_choices = kwargs.pop('problem_choices')
        super(SolutionListProblemForm, self).__init__(**kwargs)
        self.fields['problem'] = forms.TypedChoiceField(label=_('Problem'), choices=problem_choices,
                                                        coerce=int, empty_value=None, required=False)
        self.fields['problem'].widget.attrs['class'] = 'form-control'


class ActivityRecordFakeForm(forms.Form):
    mark = forms.IntegerField(required=False)
    enum = forms.TypedChoiceField(required=False, empty_value=None, choices=ActivityRecord.CHOICES, coerce=int)


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
            self.fields['person'] = forms.TypedChoiceField(label=_('User'), choices=person_choices, required=False, coerce=int)


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


'''
Queues
'''


class QueueEntryForm(forms.ModelForm):
    class Meta:
        model = QueueEntry
        fields = ['enqueue_time']

    def __init__(self, *args, **kwargs):
        user_choices = kwargs.pop('user_choices')
        super(QueueEntryForm, self).__init__(*args, **kwargs)
        self.fields['user_id'] = forms.TypedChoiceField(label=_('User'), choices=user_choices,
                                                        coerce=int, empty_value=None, required=True)


class QuizMarkFakeForm(forms.Form):
    value = forms.FloatField(required=True, localize=True)
    pk = forms.IntegerField(required=True)


class QuizSessionCommentFakeForm(forms.Form):
    comment_text = forms.CharField(required=True, max_length=65535)

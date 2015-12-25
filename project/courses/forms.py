# -*- coding: utf-8 -*-

from django import forms
from .models import Topic, Course, Activity, Assignment
from problems.models import ProblemFolder
from proglangs.models import Compiler
from mptt.forms import TreeNodeChoiceField
from django.utils.translation import ugettext_lazy as _
from common.widgets import SelectWithGrayOut


class PropertiesForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name']


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
        fields = ['name', 'kind', 'weight']


class ProblemModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.numbered_full_name()


class ProblemAssignmentForm(forms.ModelForm):
    problem = ProblemModelChoiceField(label=_('Problem'), queryset=None, required=False,
                                      widget=SelectWithGrayOut(attrs={'class': 'form-control ir-choose-problem'}))

    class Meta:
        model = Assignment
        fields = ['problem', 'criteria', 'extra_requirements', 'extra_requirements_ok']
        widgets = {
            'criteria': forms.CheckboxSelectMultiple,
            'extra_requirements': forms.Textarea(attrs={'rows': 2}),
        }


class AddExtraProblemSlotForm(forms.Form):
    penaltytopic = forms.ModelChoiceField(label=_('Topic:'), queryset=None)

from django import forms
from .models import Topic, Course, Activity
from problems.models import ProblemFolder
from proglangs.models import Compiler
from mptt.forms import TreeNodeChoiceField
from django.utils.translation import ugettext_lazy as _


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
        fields = ['name', 'problem_folder']


class ActivityForm(forms.ModelForm):
    weight = forms.FloatField(label=_('Weight coefficient'), max_value=1.0, min_value=0.0, initial=0.0,
                              widget=forms.NumberInput(attrs={'step': 0.01}))

    class Meta:
        model = Activity
        fields = ['name', 'kind', 'weight']

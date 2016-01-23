from django import forms
from .models import Problem, ProblemFolder
from mptt.forms import TreeNodeMultipleChoiceField
from django.utils.translation import ugettext_lazy as _


class ProblemForm(forms.ModelForm):
    folders = TreeNodeMultipleChoiceField(label=_('Problem folder'), queryset=ProblemFolder.objects.all())

    class Meta:
        model = Problem
        fields = ['number', 'subnumber', 'full_name', 'short_name', 'complexity', 'input_filename', 'output_filename', 'description', 'hint', 'folders']


'''
User search
'''


class ProblemSearchForm(forms.Form):
    query = forms.CharField(required=False)

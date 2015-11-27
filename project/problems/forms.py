from django.forms import ModelForm
from .models import Problem, ProblemFolder
from mptt.forms import TreeNodeMultipleChoiceField


class ProblemForm(ModelForm):
    folders = TreeNodeMultipleChoiceField(queryset=ProblemFolder.objects.all())

    class Meta:
        model = Problem
        fields = ['number', 'subnumber', 'short_name', 'full_name', 'complexity', 'folders']

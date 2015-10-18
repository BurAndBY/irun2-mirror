from django.forms import ModelForm
from .models import Problem


class ProblemForm(ModelForm):
    class Meta:
        model = Problem
        fields = ['number', 'short_name', 'full_name', 'complexity']

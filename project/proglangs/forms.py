from django.forms import ModelForm
from .models import Compiler


class CompilerForm(ModelForm):
    class Meta:
        model = Compiler
        fields = ['handle', 'famliy', 'description', 'legacy']

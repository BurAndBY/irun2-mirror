from django.forms import ModelForm
from .models import ProgrammingLanguage


class ProgrammingLanguageForm(ModelForm):
    class Meta:
        model = ProgrammingLanguage
        fields = ['handle', 'famliy', 'description', 'legacy']

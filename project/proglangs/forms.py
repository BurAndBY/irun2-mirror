from django import forms
from django.utils.translation import ugettext_lazy as _

from common.constants import EMPTY_SELECT

from proglangs.models import Compiler


class DeleteCompilerForm(forms.Form):
    replacement = forms.ModelChoiceField(label=_('Compiler for replacement'), queryset=None, required=True, empty_label=EMPTY_SELECT)

    def __init__(self, *args, **kwargs):
        current_compiler = kwargs.pop('current_compiler', None)
        super().__init__(*args, **kwargs)
        if current_compiler is not None:
            self.fields['replacement'].queryset = Compiler.objects.\
                filter(language=current_compiler.language).\
                exclude(id=current_compiler.id)

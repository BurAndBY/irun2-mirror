from django import forms
from django.utils.translation import ugettext_lazy as _


class IntranetBsuForm(forms.Form):
    FACULTY_CHOICES = (
        (3, _('Faculty of Applied Mathematics and Computer Science')),
        (2, _('Faculty of Radiophysics and Computer Technologies')),
    )
    field = forms.TypedChoiceField(label=_('Faculty'), choices=FACULTY_CHOICES, required=True)
    include_archive = forms.BooleanField(label=_('Include archive'))
    group = forms.IntegerField(label=_('Group'), required=False)

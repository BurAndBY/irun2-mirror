from django import forms
from django.utils.translation import ugettext_lazy as _


class CompareSolutionsForm(forms.Form):
    first = forms.IntegerField(min_value=0, label=_('First solution'), required=True)
    second = forms.IntegerField(min_value=0, label=_('Second solution'), required=True)
    diff = forms.BooleanField(label=_('Show only contextual differences, else show full files'), required=False)

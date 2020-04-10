from __future__ import unicode_literals

from django import forms


class ProblemSearchForm(forms.Form):
    query = forms.CharField(required=False)


class TeXForm(forms.Form):
    source = forms.CharField(required=False, max_length=32768, widget=forms.Textarea(attrs={'class': 'ir-monospace', 'rows': 20, 'autofocus': 'autofocus'}))
    renderer = forms.CharField(required=False, max_length=16)

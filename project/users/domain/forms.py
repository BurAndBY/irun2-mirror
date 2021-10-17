from django import forms
from django.utils.translation import ugettext_lazy as _

BSU_FACULTIES = [
    'Факультет прикладной математики и информатики',
]


class StudentInfoForm(forms.Form):
    ATTRIBUTE_CHOICES = [
        ('physicalDeliveryOfficeName', 'Номер зачётки'),
        ('name', 'Логин в домене'),
        ('mail', 'E-mail на bsu.by'),
    ]

    faculty = forms.ChoiceField(label=_('Faculty'), required=True, choices=((f, f) for f in BSU_FACULTIES))
    attribute = forms.ChoiceField(label=_('Value'), required=True, choices=ATTRIBUTE_CHOICES)
    names = forms.CharField(widget=forms.Textarea, required=True,
                            label=_('Data about users'),
                            help_text='Фамилия Имя Отчество')

from django import forms
from django.http import JsonResponse

from widgets import TwoPanelSelectMultiple

'''
TODO: It is slow because it loads all model instances. It can be done better.
'''


class TwoPanelModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def __init__(self, model, folder_model, url_pattern, url_params=(), queryset=None, *args, **kwargs):
        if queryset is None:
            queryset = model.objects.all()

        widget = TwoPanelSelectMultiple(folder_model, url_pattern, url_params)
        self.model = model
        self.folder_model = folder_model

        super(TwoPanelModelMultipleChoiceField, self).__init__(queryset=queryset, widget=widget, *args, **kwargs)

    @classmethod
    def ajax(cls, object_list):
        data = [{'id': obj.pk, 'name': cls.label_from_instance(obj)} for obj in object_list]
        return JsonResponse({'data': data}, safe=True)



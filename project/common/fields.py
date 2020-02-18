from django import forms
from django.http import JsonResponse
from django.utils.encoding import force_text

from common.widgets import TwoPanelSelectMultiple

'''
TODO: It is slow because it loads all model instances. It can be done better.
'''


class TwoPanelModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def __init__(self, model, folder_model, url_pattern, url_params=(), queryset=None, clean_to_list=False, *args, **kwargs):
        if queryset is None:
            queryset = model.objects.all()

        widget = TwoPanelSelectMultiple(folder_model, url_pattern, url_params)
        self.model = model
        self.folder_model = folder_model
        self.clean_to_list = clean_to_list

        super(TwoPanelModelMultipleChoiceField, self).__init__(queryset=queryset, widget=widget, *args, **kwargs)

    @classmethod
    def ajax(cls, object_list):
        data = [{'id': obj.pk, 'name': cls.label_from_instance(obj)} for obj in object_list]
        return JsonResponse({'data': data}, json_dumps_params={'ensure_ascii': False})

    def clean(self, value):
        qs = super(TwoPanelModelMultipleChoiceField, self).clean(value)
        if self.clean_to_list:
            mp = {force_text(obj.pk): obj for obj in qs.order_by()}
            return [mp[pk] for pk in value]
        else:
            return qs

from __future__ import unicode_literals

from collections import namedtuple

from django import forms
from itertools import chain

from django.core.exceptions import ImproperlyConfigured
from django.template.loader import get_template
from django.utils.encoding import force_text

from .mptt_fields import OrderedTreeNodeChoiceField


class TwoPanelSelectMultiple(forms.SelectMultiple):
    '''
    This widget loads folder contents dynamically via AJAX.
    You need to have a handle that receives HTTP GET requests on

        reverse(url_pattern, args=(*url_params, folder_id))

    and responds with JSONs like

        {
            'data': [
                {'id': folder_id1, 'name': folder_name1},
                {'id': folder_id2, 'name': folder_name2},
                {'id': folder_id3, 'name': folder_name3},
                ...
            ]
        }
    '''
    def __init__(self, folder_model, url_pattern, url_params, *args, **kwargs):
        super(TwoPanelSelectMultiple, self).__init__(*args, **kwargs)
        self.folder_model = folder_model
        self.url_pattern = url_pattern
        self.url_params = url_params

    def _make_folder_form(self, uid):
        class ObjectForm(forms.Form):
            folders = OrderedTreeNodeChoiceField(queryset=self.folder_model.objects.all(),
                                                 widget=forms.Select(attrs={'class': 'form-control'}), required=False)
        return ObjectForm(prefix=uid)

    def render(self, name, value, attrs=None, renderer=None, choices=()):
        selected_choices = set(force_text(v) for v in value)

        selected = []
        for option_value, option_label in chain(self.choices, choices):
            option_value = force_text(option_value)
            if option_value in selected_choices:
                selected.append((option_value, option_label))

        uid = 'id_{0}'.format(name)
        # TODO: "id_" is hard-coded here. This should instead use the correct
        # API to determine the ID dynamically.
        result = get_template('common/twopanelselectmultiple_widget.html').render(
            {
                'uid': uid,
                'name': name,
                'selected': selected,
                'folder_form': self._make_folder_form(uid),
                'url_pattern': self.url_pattern,
                'url_params': self.url_params,
            }
        )
        return result


Choice = namedtuple('Choice', 'pk label folders')


class ThreePanelSelectMultiple(forms.Widget):
    template_name = 'common/threepanelselectmultiple_widget.html'

    def __init__(self):
        super().__init__()
        self.inmemory_tree = None
        self.url_template = None

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if self.inmemory_tree is None or self.url_template is None:
            raise ImproperlyConfigured(self.__class__.__name__)
        context['inmemory_tree'] = self.inmemory_tree
        context['url_template'] = self.url_template
        return context

    def value_omitted_from_data(self, data, files, name):
        # An empty set of <input type="hidden"> doesn't appear in POST data, so it's
        # never known if the value is actually omitted.
        return False

    def format_value(self, value):
        # Return a value as it should appear when rendered in a template.
        return value.choices

    def value_from_datadict(self, data, files, name):
        return data.getlist(name)

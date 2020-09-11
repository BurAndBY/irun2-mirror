from collections import namedtuple

from django.core.exceptions import ImproperlyConfigured
from django.forms import Widget


Choice = namedtuple('Choice', 'pk label aux_label folders')


class ThreePanelSelectMultiple(Widget):
    '''
    This widget loads folder contents dynamically via AJAX.
    You need to have a handle that receives HTTP GET requests
    and responds with JSONs like
        {
            'items': [
                {'id': folder_id1, 'name': folder_name1},
                {'id': folder_id2, 'name': folder_name2},
                {'id': folder_id3, 'name': folder_name3},
                ...
            ]
        }
    '''

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

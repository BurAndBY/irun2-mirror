from django.forms.widgets import Textarea


class TeXTextarea(Textarea):
    template_name = 'tex/tex_textarea_widget.html'

    def __init__(self, attrs=None):
        default_attrs = {'class': 'ir-monospace'}
        if attrs is not None:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

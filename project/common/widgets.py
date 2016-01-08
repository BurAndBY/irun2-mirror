from __future__ import unicode_literals

from django import forms
from itertools import chain

from django.utils.safestring import mark_safe
from django.utils.encoding import force_text
from django.utils.html import conditional_escape, format_html

from mptt.forms import TreeNodeChoiceField


class SelectWithGrayOut(forms.Select):
    NORMAL_CLASS = 'ir-opt'
    GRAYED_CLASS = 'ir-opt-gray'

    '''
    params:
        hl_suffix: suffix to be appended to option text if option is highlighted
    '''
    def __init__(self, hl_suffix=None, *args, **kwargs):
        super(SelectWithGrayOut, self).__init__(*args, **kwargs)

        self._hl_suffix = None if hl_suffix is None else force_text(hl_suffix)

        self._grayed_out = {}

    def gray_out(self, value, reason=None):
        self._grayed_out[force_text(value)] = force_text(reason) if reason is not None else None

    def render_option(self, selected_choices, option_value, option_label):
        if option_value is None:
            option_value = ''
        option_value = force_text(option_value)

        # define selected_html
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''

        if option_value in self._grayed_out:
            css_class = SelectWithGrayOut.GRAYED_CLASS
        else:
            css_class = SelectWithGrayOut.NORMAL_CLASS

        option_label = force_text(option_label)

        reason = self._grayed_out.get(option_value)
        if reason is not None:
            label_html = format_html('{} &mdash; {}', option_label, reason)
        else:
            label_html = conditional_escape(option_label)

        return format_html('<option class="{}" value="{}"{}>{}</option>',
                           css_class,
                           option_value,
                           selected_html,
                           label_html)

# get_template is what we need for loading up the template for parsing.
from django.template.loader import get_template

# Templates in Django need a "Context" to parse with, so we'll borrow this.
# "Context"'s are really nothing more than a generic dict wrapped up in a
# neat little function call.
from django.template import Context


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
            folders = TreeNodeChoiceField(queryset=self.folder_model.objects.all(),
                                          widget=forms.Select(attrs={'class': 'form-control'}))
        return ObjectForm(prefix=uid)

    def render(self, name, value, attrs=None, choices=()):
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
            Context({
                'uid': uid,
                'name': name,
                'selected': selected,
                'folder_form': self._make_folder_form(uid),
                'url_pattern': self.url_pattern,
                'url_params': self.url_params,
            })
        )
        return result

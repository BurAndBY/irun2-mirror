from __future__ import unicode_literals

from django import forms

from django.utils.safestring import mark_safe
from django.utils.encoding import force_text
from django.utils.html import conditional_escape, format_html


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

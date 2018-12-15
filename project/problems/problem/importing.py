import re

from django import forms
from django.utils.translation import ugettext_lazy as _


class FileNamingScheme(object):
    def guess_base_name(self, filename):
        raise NotImplementedError()

    def get_input_name(self, base_name):
        raise NotImplementedError()

    def get_output_name(self, base_name):
        raise NotImplementedError()


class SimpleNamingScheme(FileNamingScheme):
    def __init__(self, input_ext, output_ext):
        self._input_ext = ('.' + input_ext) if input_ext else ''
        self._output_ext = ('.' + output_ext) if output_ext else ''

        if not self._input_ext and not self._output_ext:
            raise ValueError('either input or output extension must be provided')

        if self._input_ext and self._output_ext:
            if (self._input_ext.endswith(self._output_ext) or self._output_ext.endswith(self._input_ext)):
                raise ValueError('conflicting extensions')

    def guess_base_name(self, filename):
        if self._input_ext and filename.endswith(self._input_ext):
            return filename[:-len(self._input_ext)]
        if self._output_ext and filename.endswith(self._output_ext):
            return filename[:-len(self._output_ext)]
        if not self._input_ext:
            return filename
        if not self._output_ext:
            return filename
        return None

    def get_input_name(self, base_name):
        return base_name + self._input_ext

    def get_output_name(self, base_name):
        return base_name + self._output_ext


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)]


def extract_tests(filenames, input_ext, output_ext):
    '''
    Returns a list of tuples (input name, output name).
    '''
    scheme = SimpleNamingScheme(input_ext, output_ext)
    base_names = set()

    for filename in filenames:
        base_name = scheme.guess_base_name(filename)
        if base_name is None:
            raise forms.ValidationError(
                _('Unknown file found in the archive: %(name)s'),
                code='unknown',
                params={'name': filename}
            )
        base_names.add(base_name)

    base_names = sorted(base_names, key=natural_sort_key)
    filenames = set(filenames)

    def _check(filename):
        if filename not in filenames:
            raise forms.ValidationError(
                _('File not found in the archive: %(name)s'),
                code='not_found',
                params={'name': filename}
            )

    tests = []
    for base_name in base_names:
        input_name = scheme.get_input_name(base_name)
        output_name = scheme.get_output_name(base_name)
        _check(input_name)
        _check(output_name)
        tests.append((input_name, output_name))
    return tests

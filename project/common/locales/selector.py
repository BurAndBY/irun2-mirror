from collections import namedtuple

from django.utils.text import format_lazy
from django.utils.translation import get_language_info, get_language
from django.utils.translation import gettext_lazy as _

from .best import find_best

LangInfo = namedtuple('LangInfo', ['code', 'name', 'query_string'])


def _select_lang(langs_available, request_get, param_name):
    if len(langs_available) == 0:
        return None

    param = request_get.get(param_name)
    if param in langs_available:
        return param

    return find_best(langs_available, get_language())


class LanguageSelector:
    def __init__(self, langs_available, request_get, param_name='lang'):
        self.langs_available = sorted(langs_available)
        self.request_get = request_get.copy()
        self.param_name = param_name

        self.request_get.pop(self.param_name, None)

        self.current_lang = _select_lang(self.langs_available, request_get, param_name)
        self.default_lang = _select_lang(self.langs_available, {}, param_name)

    def get_current_lang(self):
        return self.current_lang

    def list_langs(self):
        return [LangInfo(code, self._get_name(code), self._get_query_string(code)) for code in self.langs_available]

    def _get_name(self, code):
        if code == '':
            return _('Unknown')
        li = get_language_info(code)
        return format_lazy('{} ({})', li['name_translated'], code)

    def _get_query_string(self, code):
        params = self.request_get.copy()
        if code != self.default_lang:
            params[self.param_name] = code

        if params:
            return '?' + params.urlencode()
        else:
            return '.'

    def __bool__(self):
        return len(self.langs_available) > 1

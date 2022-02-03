from django.conf import settings
from django.utils import translation

from common.tree.key import ROOT


def _language_translated(language):
    with translation.override(language):
        return translation.gettext('Language')


def system_name(request):
    return {
        'system_full_name': 'Insight Runner 2',
        'system_short_name': 'iRunner 2',
        'external_links': settings.EXTERNAL_LINKS,
        'root_folder': ROOT,
        'location': settings.LOCATION,
        'language_switcher_link_text': '\u2009/\u2009'.join(_language_translated(lang) for lang, _ in settings.LANGUAGES)
    }

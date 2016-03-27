from django.utils.translation import ugettext_lazy as _


class Tab(object):
    def __init__(self, key, name, icon, url_pattern, subtab=False):
        self.key = key
        self.name = name
        self.icon = icon
        self.url_pattern = url_pattern
        self.subtab = subtab


class TabManager(object):
    def __init__(self, tabs):
        self.tabs = tabs

    def get(self, key):
        for tab in self.tabs:
            if tab.key == key:
                return tab
        return None


def create_problem_tab_manager():
    tabs = [
        Tab('properties', _('Properties'), 'cog', 'problems:properties'),
        Tab('folders', _('Folders'), 'folder-open', 'problems:folders'),
        Tab('statement', _('Statement'), 'file', 'problems:statement'),
        Tab('tests', _('Tests'), 'list-alt', 'problems:tests'),
        Tab('validator', _('Validator'), 'ok', 'problems:validator'),
        Tab('solutions', _('Solutions'), 'tasks', 'problems:solutions'),
        Tab('files', _('Files'), 'paperclip', 'problems:files'),
        Tab('tex', _('TeX editor'), 'text-size', 'problems:tex', subtab=True),
        Tab('pictures', _('Pictures'), 'picture', 'problems:pictures', subtab=True),
        Tab('submit', _('Submit solution'), 'send', 'problems:submit'),
    ]
    return TabManager(tabs)

PROBLEM_TAB_MANAGER = create_problem_tab_manager()

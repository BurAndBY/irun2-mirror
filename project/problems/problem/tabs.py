from django.utils.translation import ugettext_lazy as _

from problems.problem.permissions import SingleProblemPermissions as SPP


class Tab(object):
    def __init__(self, key, name, icon, url_pattern, subtab=False, permissions=0):
        self.key = key
        self.name = name
        self.icon = icon
        self.url_pattern = url_pattern
        self.subtab = subtab
        self.permissions = permissions


class TabManager(object):
    def __init__(self, tabs, permissions=None):
        if permissions is None:
            self.tabs = tabs
        else:
            self.tabs = [tab for tab in tabs if permissions.check(tab.permissions)]

    def get(self, key):
        for tab in self.tabs:
            if tab.key == key:
                return tab
        return None


PROBLEM_TABS = [
    Tab('name', _('Name'), 'tag', 'problems:name', permissions=SPP.EDIT),
    Tab('properties', _('Properties'), 'cog', 'problems:properties', permissions=SPP.EDIT),
    Tab('access', _('Access'), 'lock', 'problems:access'),
    Tab('folders', _('Folders'), 'folder-open', 'problems:folders', permissions=SPP.MOVE),
    Tab('statement', _('Statement'), 'file', 'problems:statement'),
    Tab('tests', _('Tests'), 'list-alt', 'problems:tests'),
    Tab('validator', _('Validator'), 'ok', 'problems:validator', permissions=SPP.EDIT),
    Tab('solutions', _('Solutions'), 'tasks', 'problems:solutions'),
    Tab('challenges', _('Challenges'), 'wrench', 'problems:challenges'),
    Tab('rejudges', _('Rejudges'), 'repeat', 'problems:rejudges'),
    Tab('files', _('Files'), 'paperclip', 'problems:files'),
    Tab('tex', _('TeX editor'), 'text-size', 'problems:tex', subtab=True),
    Tab('pictures', _('Pictures'), 'picture', 'problems:pictures', subtab=True),
    Tab('submit', _('Submit solution'), 'send', 'problems:submit'),
]

# -*- coding: utf-8 -*-

from .models import Problem, ProblemFolder

from common.folderutils import ROOT, cast_id
from django.core.urlresolvers import reverse
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

PARAM = u'nav-folder'


class NavigatorImpl(object):
    def __init__(self, folder, problem_id, problems_list):
        self.folder = folder
        self.pos = problems_list.index(problem_id)
        self.problems_list = problems_list

        self._query_string = '?' + urlencode(self.iterate_query_params())

    def get_folder_url(self):
        return reverse('problems:show_folder', kwargs={'folder_id_or_root': self.folder.id if self.folder is not None else ROOT})

    def get_folder_name(self):
        return self.folder.name if self.folder is not None else _('Problems')

    def get_prev(self):
        n = self.get_total_count()
        return self.problems_list[(self.pos + n - 1) % n]

    def get_next(self):
        n = self.get_total_count()
        return self.problems_list[(self.pos + 1) % n]

    def get_query_string(self):
        return self._query_string

    def iterate_query_params(self):
        folder_id = unicode(self.folder.id) if self.folder is not None else ROOT
        return [(PARAM, folder_id)]

    def get_current_index(self):
        return self.pos + 1

    def get_total_count(self):
        return len(self.problems_list)


def init(problem_id, request_get):
    if PARAM not in request_get:
        return
    try:
        folder_id = cast_id(request_get[PARAM])
    except:
        return

    if folder_id is None:
        # fake root folder
        folder = None
    else:
        folder = ProblemFolder.objects.filter(pk=folder_id).first()
        if folder is None:
            return

    problems_list = Problem.objects.filter(folders__id=folder_id).values_list('id', flat=True)
    problems_list = list(problems_list)
    if problem_id not in problems_list:
        return

    return NavigatorImpl(folder, problem_id, problems_list)


class Navigator(object):
    def __init__(self, problem_id, request_get):
        self.impl = init(problem_id, request_get)

    def query_string(self):
        return u'' if self.impl is None else self.impl.get_query_string()

    def query_params(self):
        return [] if self.impl is None else self.impl.iterate_query_params()

    def impl(self):
        return self.impl

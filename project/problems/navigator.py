# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.urls import reverse
from django.utils.http import urlencode

from common.tree.key import FolderId
from problems.loader import ProblemFolderLoader

PARAM = 'nav-folder'


def _create_query_string(params):
    return '?' + urlencode(params)


def make_folder_query_string(folder_id):
    return _create_query_string([(PARAM, FolderId.to_string(folder_id))])


class NavigatorImpl(object):
    def __init__(self, node, problem_id, problems_list):
        self.node = node
        self.pos = problems_list.index(problem_id)
        self.problems_list = problems_list
        self._query_string = _create_query_string(self.iterate_query_params())

    def get_folder_url(self):
        return reverse('problems:show_folder', kwargs={'folder_id_or_root': FolderId.to_string(self.node.id)})

    def get_folder_name(self):
        return self.node.name

    def get_prev(self):
        n = self.get_total_count()
        return self.problems_list[(self.pos + n - 1) % n]

    def get_next(self):
        n = self.get_total_count()
        return self.problems_list[(self.pos + 1) % n]

    def get_query_string(self):
        return self._query_string

    def iterate_query_params(self):
        folder_id_or_root = FolderId.to_string(self.node.id)
        return [(PARAM, folder_id_or_root)]

    def get_current_index(self):
        return self.pos + 1

    def get_total_count(self):
        return len(self.problems_list)


def init(problem_id, request_user, request_get):
    if PARAM not in request_get:
        return
    try:
        folder_id = FolderId.from_string(request_get[PARAM])
    except (KeyError, ValueError):
        return

    node = ProblemFolderLoader.load_node(request_user, folder_id)
    if node is None:
        return
    qs = ProblemFolderLoader.get_folder_content(request_user, node)
    problems_list = qs.values_list('id', flat=True)
    problems_list = list(problems_list)
    if problem_id not in problems_list:
        return

    return NavigatorImpl(node, problem_id, problems_list)


class Navigator(object):
    def __init__(self, problem_id, request_user, request_get):
        self.impl = init(problem_id, request_user, request_get)

    def query_string(self):
        return '' if self.impl is None else self.impl.get_query_string()

    def query_params(self):
        return [] if self.impl is None else self.impl.iterate_query_params()

    def impl(self):
        return self.impl

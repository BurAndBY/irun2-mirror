# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import functools
import json
import mimetypes
import operator
import re

from django.urls import reverse
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import generic
from mptt.templatetags.mptt_tags import cache_tree_children

from cauth.mixins import StaffMemberRequiredMixin, LoginRequiredMixin
from common.folderutils import _fancytree_recursive_node_to_dict
from common.pagination import paginate

from storage.storage import create_storage
from storage.utils import serve_resource

from problems.calcpermissions import get_problems_queryset
from problems.forms import (
    ProblemSearchForm,
    TeXForm,
)
from problems.models import Problem, ProblemRelatedFile, ProblemFolder
from problems.statement import StatementRepresentation
from problems.texrenderer import render_tex


'''
Problem statement
'''


class ProblemStatementMixin(object):
    @staticmethod
    def _normalize(filename):
        return filename.rstrip('/')

    def is_aux_file(self, filename):
        return filename is not None and len(ProblemStatementMixin._normalize(filename)) > 0

    def serve_aux_file(self, request, problem_id, filename):
        filename = ProblemStatementMixin._normalize(filename)

        related_file = get_object_or_404(ProblemRelatedFile, problem_id=problem_id, filename=filename)
        mime_type, encoding = mimetypes.guess_type(filename)

        content_type = mime_type
        if content_type == 'text/html':
            content_type += '; charset=utf-8'

        return serve_resource(request, related_file.resource_id, content_type=content_type)

    def make_statement(self, problem):
        related_files = problem.problemrelatedfile_set.all()

        tex_statement_resource_id = None
        renderer = None
        html_statement_name = None

        for related_file in related_files:
            ft = related_file.file_type

            if ft == ProblemRelatedFile.STATEMENT_HTML:
                if html_statement_name is None:
                    html_statement_name = related_file.filename

            elif ft == ProblemRelatedFile.STATEMENT_TEX_TEX2HTML:
                if tex_statement_resource_id is None:
                    tex_statement_resource_id = related_file.resource_id
                    renderer = 'tex2html'

            elif ft == ProblemRelatedFile.STATEMENT_TEX_PYLIGHTEX:
                if tex_statement_resource_id is None:
                    tex_statement_resource_id = related_file.resource_id
                    renderer = 'pylightex'

        st = StatementRepresentation(problem)

        # TeX
        if st.is_empty and tex_statement_resource_id is not None:
            storage = create_storage()
            tex_data = storage.represent(tex_statement_resource_id)
            if tex_data is not None and tex_data.complete_text is not None:
                render_result = render_tex(tex_data.complete_text, problem.input_filename, problem.output_filename, renderer=renderer)
                st.content = render_result.output

        # HTML
        if st.is_empty and html_statement_name is not None:
            st.iframe_name = html_statement_name

        return st


'''
Alternative folder tree
'''


class FancyTreeMixin(object):
    @staticmethod
    def _list_folders():
        root_nodes = cache_tree_children(ProblemFolder.objects.all())
        dicts = []
        for n in root_nodes:
            dicts.append(_fancytree_recursive_node_to_dict(n))

        return json.dumps(dicts)

    @staticmethod
    def _list_folder_contents(folder_id):
        problems = Problem.objects.filter(folders__id=folder_id)
        result = [[str(p.id), p.full_name] for p in problems]
        return result


class ShowTreeView(StaffMemberRequiredMixin, FancyTreeMixin, generic.View):
    def get(self, request):
        tree_data = self._list_folders()
        return render(request, 'problems/tree.html', {
            'tree_data': tree_data
        })


class ShowTreeFolderView(StaffMemberRequiredMixin, FancyTreeMixin, generic.View):
    def get(self, request, folder_id):
        folder = get_object_or_404(ProblemFolder, pk=folder_id)
        tree_data = self._list_folders()
        return render(request, 'problems/tree.html', {
            'tree_data': tree_data,
            'cur_folder_id': folder.id,
            'cur_folder_name': folder.name,
            'table_data': json.dumps(self._list_folder_contents(folder_id))
        })


class ShowTreeFolderJsonView(StaffMemberRequiredMixin, FancyTreeMixin, generic.View):
    def get(self, request, folder_id):
        folder = ProblemFolder.objects.filter(pk=folder_id).first()
        name = folder.name if folder is not None else ''
        data = self._list_folder_contents(folder_id)
        return JsonResponse({'id': folder_id, 'name': name, 'data': data}, json_dumps_params={'ensure_ascii': False})


'''
All problems: search
'''


class SearchView(LoginRequiredMixin, generic.View):
    template_name = 'problems/list_search.html'
    paginate_by = 12
    number_regex = re.compile(r'^(?P<number>\d+)(\.(?P<subnumber>\d+))?$')

    def _create_posfilter(self, word):
        m = self.number_regex.match(word)
        if m:
            posfilter = Q(number=m.group('number'))
            if m.group('subnumber') is not None:
                posfilter = posfilter & Q(subnumber=m.group('subnumber'))
            else:
                posfilter = posfilter | Q(id=m.group('number'))
        else:
            posfilter = Q(full_name__icontains=word)
        return posfilter

    def get_queryset(self, query=None):
        queryset = get_problems_queryset(self.request.user)
        if query is not None:
            terms = query.split()
            if terms:
                queryset = queryset.filter(functools.reduce(operator.and_, (self._create_posfilter(term) for term in terms)))
        return queryset

    def get(self, request):
        form = ProblemSearchForm(request.GET)
        if form.is_valid():
            queryset = self.get_queryset(form.cleaned_data['query'])
        else:
            queryset = self.get_queryset()

        context = paginate(request, queryset, self.paginate_by)
        context['active_tab'] = 'search'
        context['form'] = form
        return render(request, self.template_name, context)


'''
TeX editor playground
'''


class TeXView(StaffMemberRequiredMixin, generic.View):
    template_name = 'problems/tex_playground.html'

    def get(self, request):
        form = TeXForm()
        context = {
            'form': form,
            'render_url': reverse('problems:tex_playground_render'),
        }
        return render(request, self.template_name, context)


def get_tex_preview(form, problem=None):
    result = {}
    if form.is_valid():
        source = form.cleaned_data['source']
        renderer = form.cleaned_data['renderer']

        if problem is None:
            render_result = render_tex(source, renderer=renderer)
        else:
            render_result = render_tex(source, input_filename=problem.input_filename, output_filename=problem.output_filename,
                                       renderer=renderer)
        result['output'] = render_result.output
        result['log'] = render_result.log
    else:
        log_lines = []
        for field, errors in form.errors.items():
            log_lines.extend('— {0}'.format(e) for e in errors)
        result['log'] = '\n'.join(log_lines)
    return result


class TeXRenderView(StaffMemberRequiredMixin, generic.View):
    def post(self, request):
        form = TeXForm(request.POST)
        return JsonResponse(get_tex_preview(form), json_dumps_params={'ensure_ascii': False})

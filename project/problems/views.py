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
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from cauth.mixins import StaffMemberRequiredMixin, ProblemEditorMemberRequiredMixin
from common.folderutils import make_fancytree_json
from common.locale.selector import LanguageSelector
from common.pagination import paginate
from common.tree.inmemory import Tree

from storage.storage import create_storage
from storage.utils import serve_resource

from problems.calcpermissions import get_problem_ids_queryset
from problems.forms import (
    ProblemSearchForm,
    TeXTechForm,
    TeXRelatedFileForm,
)
from problems.models import Problem, ProblemRelatedFile, ProblemFolder, ProblemAccess, ProblemFolderAccess
from problems.statement import StatementRepresentation
from problems.texrenderer import render_tex


'''
Problem statement
'''


class Statement(object):
    def __init__(self):
        self.tex_statement_resource_id = None
        self.renderer = None
        self.html_statement_name = None

    def consume(self, related_file):
        ft = related_file.file_type

        if ft == ProblemRelatedFile.STATEMENT_HTML:
            if self.html_statement_name is None:
                self.html_statement_name = related_file.filename

        elif ft == ProblemRelatedFile.STATEMENT_TEX_TEX2HTML:
            if self.tex_statement_resource_id is None:
                self.tex_statement_resource_id = related_file.resource_id
                self.renderer = 'tex2html'

        elif ft == ProblemRelatedFile.STATEMENT_TEX_PYLIGHTEX:
            if self.tex_statement_resource_id is None:
                self.tex_statement_resource_id = related_file.resource_id
                self.renderer = 'pylightex'

    def represent(self, problem, selector):
        st = StatementRepresentation(problem)
        st.lang_selector = selector

        # TeX
        if st.is_empty and self.tex_statement_resource_id is not None:
            storage = create_storage()
            tex_data = storage.represent(self.tex_statement_resource_id)
            if tex_data is not None and tex_data.complete_text is not None:
                render_result = render_tex(tex_data.complete_text, problem.input_filename, problem.output_filename, renderer=self.renderer)
                st.content = render_result.output

        # HTML
        if st.is_empty and self.html_statement_name is not None:
            st.iframe_name = self.html_statement_name

        return st

    def empty(self):
        return self.tex_statement_resource_id is None and self.html_statement_name is None


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
        lang_to_stmt = {}

        for related_file in related_files:
            lang_to_stmt.setdefault(related_file.language, Statement()).consume(related_file)

        lang_to_stmt = {k: v for k, v in lang_to_stmt.items() if not v.empty()}

        if lang_to_stmt:
            selector = LanguageSelector(lang_to_stmt.keys(), self.request.GET, 'stmt-lang')
            stmt = lang_to_stmt[selector.get_current_lang()]
            return stmt.represent(problem, selector)

        # empty statement
        return StatementRepresentation(problem)

    def make_tutorial(self, problem):
        file = problem.problemrelatedfile_set.filter(file_type=ProblemRelatedFile.TUTORIAL_TEX_PYLIGHTEX).first()
        st = StatementRepresentation(problem)

        # TeX
        if file is not None:
            storage = create_storage()
            tex_data = storage.represent(file.resource_id)
            if tex_data is not None and tex_data.complete_text is not None:
                render_result = render_tex(tex_data.complete_text, problem.input_filename, problem.output_filename, renderer='pylightex')
                st.content = render_result.output
        return st


'''
Alternative folder tree
'''


class FancyTreeMixin(object):
    @staticmethod
    def _list_folders(user):
        tree = Tree.load(_('Problems'), ProblemFolder, None, user)
        return make_fancytree_json(tree)

    @staticmethod
    def _list_folder_contents(folder_id):
        problems = Problem.objects.filter(folders__id=folder_id)
        result = [[str(p.id), p.full_name] for p in problems]
        return result


class ShowTreeView(StaffMemberRequiredMixin, FancyTreeMixin, generic.View):
    def get(self, request):
        tree_data = self._list_folders(request.user)
        return render(request, 'problems/tree.html', {
            'tree_data': tree_data
        })


class ShowTreeFolderView(StaffMemberRequiredMixin, FancyTreeMixin, generic.View):
    def get(self, request, folder_id):
        folder = get_object_or_404(ProblemFolder, pk=folder_id)
        tree_data = self._list_folders(request.user)
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


class SearchView(ProblemEditorMemberRequiredMixin, generic.View):
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
        queryset = Problem.objects.filter(id__in=get_problem_ids_queryset(self.request.user))
        if query is not None:
            terms = query.split()
            if terms:
                queryset = queryset.filter(functools.reduce(operator.and_, (self._create_posfilter(term) for term in terms)))
        return queryset.order_by('id')

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


class DefaultView(generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse('problems:search')


'''
TeX editor playground
'''


class TeXView(StaffMemberRequiredMixin, generic.View):
    template_name = 'problems/tex_playground.html'

    def get(self, request):
        form = TeXRelatedFileForm()
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
        form = TeXTechForm(request.POST)
        return JsonResponse(get_tex_preview(form), json_dumps_params={'ensure_ascii': False})


class AccessBrowserView(StaffMemberRequiredMixin, generic.View):
    template_name = 'problems/access_browser.html'

    def get(self, request):
        context = {
            'individual_access_records': ProblemAccess.objects.all().select_related('problem', 'user'),
            'group_access_records': ProblemFolderAccess.objects.all().select_related('folder', 'group'),
        }
        return render(request, self.template_name, context)

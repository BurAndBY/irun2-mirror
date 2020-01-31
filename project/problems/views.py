# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import functools
import json
import mimetypes
import operator
import re

from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db import transaction
from django.db.models import Q
from django.http import Http404, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.views import generic
from django.utils.translation import ugettext_lazy as _
from mptt.templatetags.mptt_tags import cache_tree_children
from django.core.exceptions import PermissionDenied

from cauth.mixins import StaffMemberRequiredMixin, LoginRequiredMixin
from common.access import Permissions, PermissionCheckMixin
from common.folderutils import lookup_node_ex, cast_id, ROOT, _fancytree_recursive_node_to_dict
from common.pageutils import paginate
from common.views import IRunnerListView
from courses.models import Course
from proglangs.models import Compiler

from storage.storage import create_storage
from storage.utils import serve_resource

from problems.calcpermissions import get_problems_queryset
from problems.forms import (
    ProblemSearchForm,
    TeXForm,
    ProblemFolderForm,
    PolygonImportForm,
    SimpleProblemForm,
)
from problems.models import Problem, ProblemRelatedFile, ProblemFolder
from problems.navigator import make_folder_query_string
from problems.polygon import import_full_package
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
        return JsonResponse({'id': folder_id, 'name': name, 'data': data}, safe=True)

'''
All problems: folders
'''


class ProblemPermissions(Permissions):
    VIEW_ALL_PROBLEMS = 1 << 0
    CREATE_PROBLEMS = 1 << 1
    MANAGE_FOLDERS = 1 << 2
    ALL = VIEW_ALL_PROBLEMS | CREATE_PROBLEMS | MANAGE_FOLDERS


class ProblemPermissionCheckMixin(PermissionCheckMixin):
    def _make_permissions(self, user):
        if user.is_staff:
            return ProblemPermissions(ProblemPermissions.ALL)
        if user.userprofile.has_access_to_problems:
            return ProblemPermissions()


class BrowseProblemsAccessMixin(LoginRequiredMixin, ProblemPermissionCheckMixin):
    pass


class ProblemFolderMixin(object):
    def get_context_data(self, **kwargs):
        context = super(ProblemFolderMixin, self).get_context_data(**kwargs)
        cached_trees = ProblemFolder.objects.all().get_cached_trees()
        node_ex = lookup_node_ex(self.kwargs['folder_id_or_root'], cached_trees)

        context['cached_trees'] = cached_trees
        context['folder'] = node_ex.object
        context['folder_id'] = node_ex.folder_id
        context['active_tab'] = 'folders'
        context['editable_folder'] = node_ex.object is not None
        return context


class ShowFolderView(BrowseProblemsAccessMixin, ProblemFolderMixin, IRunnerListView):
    template_name = 'problems/list_folder.html'
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super(ShowFolderView, self).get_context_data(**kwargs)
        folder_id_or_root = self.kwargs['folder_id_or_root']
        if folder_id_or_root:
            context['query_string'] = make_folder_query_string(folder_id_or_root)
        return context

    def get_queryset(self):
        folder_id = cast_id(self.kwargs['folder_id_or_root'])
        return get_problems_queryset(self.request.user).filter(folders__id=folder_id)


class CreateFolderView(BrowseProblemsAccessMixin, ProblemFolderMixin, generic.FormView):
    template_name = 'problems/list_folder_form.html'
    form_class = ProblemFolderForm
    requirements = ProblemPermissions.MANAGE_FOLDERS

    def get_context_data(self, **kwargs):
        context = super(CreateFolderView, self).get_context_data(**kwargs)
        context['form_name'] = _('Create folder')
        context['show_parent'] = True
        return context

    def form_valid(self, form):
        folder_id_or_root = self.kwargs['folder_id_or_root']
        obj = form.save(commit=False)
        obj.parent_id = cast_id(folder_id_or_root)
        obj.save()
        return redirect('problems:show_folder', folder_id_or_root)


class UpdateFolderView(BrowseProblemsAccessMixin, ProblemFolderMixin, generic.UpdateView):
    template_name = 'problems/list_folder_form.html'
    form_class = ProblemFolderForm
    requirements = ProblemPermissions.MANAGE_FOLDERS

    def get_context_data(self, **kwargs):
        context = super(UpdateFolderView, self).get_context_data(**kwargs)
        context['form_name'] = _('Folder properties')
        context['show_parent'] = False
        return context

    def get_success_url(self):
        folder_id_or_root = self.kwargs['folder_id_or_root']
        return reverse('problems:show_folder', kwargs={'folder_id_or_root': folder_id_or_root})

    def get_object(self):
        folder_id = cast_id(self.kwargs['folder_id_or_root'])
        if folder_id is not None:
            return ProblemFolder.objects.get(pk=folder_id)
        else:
            raise Http404('no folder found')


class DeleteFolderView(BrowseProblemsAccessMixin, ProblemFolderMixin, generic.base.ContextMixin, generic.View):
    template_name = 'problems/list_folder_confirm_delete.html'
    requirements = ProblemPermissions.MANAGE_FOLDERS

    def list_courses(self, folder):
        subfolder_ids = folder.get_descendants(include_self=True).values_list('id', flat=True)
        return list(Course.objects.filter(topic__problem_folder_id__in=subfolder_ids).distinct())

    def get(self, request, folder_id_or_root):
        folder_id = cast_id(folder_id_or_root)
        folder = get_object_or_404(ProblemFolder, pk=folder_id)
        context = self.get_context_data(course_list=self.list_courses(folder))
        return render(request, self.template_name, context)

    def post(self, request, folder_id_or_root):
        folder_id = cast_id(folder_id_or_root)
        folder = get_object_or_404(ProblemFolder, pk=folder_id)
        parent_id = folder.parent_id
        with transaction.atomic():
            folder.delete()
        return redirect('problems:show_folder', parent_id if parent_id is not None else ROOT)


class ImportFromPolygonView(BrowseProblemsAccessMixin, ProblemFolderMixin, generic.base.ContextMixin, generic.View):
    template_name = 'problems/list_import_from_polygon.html'
    requirements = ProblemPermissions.CREATE_PROBLEMS

    def get(self, request, folder_id_or_root):
        # TODO: better way to select default compiler (remember last used?)
        compiler = Compiler.objects.filter(description__contains='GNU C++', default_for_courses=True).first()
        form = PolygonImportForm(initial={'compiler': compiler})

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, folder_id_or_root):
        form = PolygonImportForm(request.POST, request.FILES)
        has_error = False
        validation_error = None
        exception = None
        exception_type = None

        if form.is_valid():
            folder_id = cast_id(folder_id_or_root)
            try:
                with transaction.atomic():
                    import_full_package(form.cleaned_data['upload'], form.cleaned_data['language'], form.cleaned_data['compiler'], request.user, folder_id)
            except ValidationError as e:
                has_error = True
                validation_error = e
            except Exception as e:
                has_error = True
                exception = e
                exception_type = type(e).__name__

            if not has_error:
                return redirect('problems:show_folder', folder_id if folder_id is not None else ROOT)

        context = self.get_context_data(form=form, has_error=has_error, validation_error=validation_error, exception=exception, exception_type=exception_type)
        return render(request, self.template_name, context)


class CreateProblemView(BrowseProblemsAccessMixin, ProblemFolderMixin, generic.FormView):
    template_name = 'problems/list_folder_form.html'
    form_class = SimpleProblemForm
    requirements = ProblemPermissions.CREATE_PROBLEMS

    def get_context_data(self, **kwargs):
        context = super(CreateProblemView, self).get_context_data(**kwargs)
        context['form_name'] = _('New problem')
        context['show_parent'] = True
        return context

    def form_valid(self, form):
        folder_id_or_root = self.kwargs['folder_id_or_root']
        folder_id = cast_id(folder_id_or_root)
        with transaction.atomic():
            problem = form.save()
            if folder_id is not None:
                problem.folders.add(folder_id)

        url = reverse('problems:properties', kwargs={'problem_id': problem.id})
        url += make_folder_query_string(folder_id_or_root)
        return HttpResponseRedirect(url)

'''
All problems: search
'''


class SearchView(BrowseProblemsAccessMixin, generic.View):
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
        return JsonResponse(get_tex_preview(form))

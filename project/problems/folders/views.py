# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from cauth.acl.mixins import ShareWithGroupMixin
from cauth.mixins import LoginRequiredMixin
from common.access import Permissions, PermissionCheckMixin
from common.folderutils import lookup_node_ex, cast_id, ROOT
from common.pagination.views import IRunnerListView
from courses.models import Course
from proglangs.models import Compiler

from problems.calcpermissions import get_problems_queryset
from problems.models import ProblemFolder, ProblemFolderAccess
from problems.navigator import make_folder_query_string
from .forms import (
    ProblemFolderForm,
    PolygonImportForm,
    SimpleProblemForm,
)
from .polygon import import_full_package


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


class FolderAccessView(BrowseProblemsAccessMixin, ProblemFolderMixin, ShareWithGroupMixin, generic.base.ContextMixin, generic.View):
    template_name = 'problems/list_folder_access.html'
    form_class = ProblemFolderForm
    requirements = ProblemPermissions.MANAGE_FOLDERS

    access_model = ProblemFolderAccess
    access_model_object_field = 'folder'

    def get(self, request, folder_id_or_root):
        folder_id = cast_id(folder_id_or_root)
        folder = get_object_or_404(ProblemFolder, pk=folder_id)
        context = self._get(request, folder)
        return render(request, self.template_name, self.get_context_data(**context))

    def post(self, request, folder_id_or_root):
        folder_id = cast_id(folder_id_or_root)
        folder = get_object_or_404(ProblemFolder, pk=folder_id)
        success, context = self._post(request, folder)
        if success:
            return redirect('problems:folder_access', folder_id if folder_id is not None else ROOT)
        return render(request, self.template_name, self.get_context_data(**context))


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

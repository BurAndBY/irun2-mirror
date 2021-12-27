# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from cauth.acl.accessmode import AccessMode
from cauth.acl.mixins import ShareFolderWithGroupMixin
from cauth.mixins import ProblemEditorMemberRequiredMixin
from common.access import Permissions, PermissionCheckMixin
from common.pagination.views import IRunnerListView
from common.tree.key import FolderId
from common.tree.mixins import FolderMixin
from courses.models import Course
from proglangs.models import Compiler

from problems.loader import ProblemFolderLoader
from problems.models import Problem, ProblemFolder, ProblemFolderAccess
from problems.navigator import make_folder_query_string

from problems.folders.forms import ProblemFolderForm, PolygonImportForm, SimpleProblemForm
from problems.folders.polygon import import_full_package


class FolderPermissions(Permissions):
    VIEW_PROBLEMS = 1 << 0
    MANAGE_FOLDERS = 1 << 1
    GRANT_ACCESS = 1 << 2


class ProblemFolderMixin(FolderMixin):
    loader_cls = ProblemFolderLoader

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'folders'
        return context


class FolderPermissionCheckMixin(PermissionCheckMixin):
    def _make_permissions(self, user):
        if user.is_staff:
            return FolderPermissions().allow_all()
        if self.node.access == AccessMode.WRITE:
            return FolderPermissions().allow_view_problems().allow_manage_folders()
        if self.node.access == AccessMode.MODIFY:
            return FolderPermissions().allow_view_problems()
        if self.node.access == AccessMode.READ:
            return FolderPermissions().allow_view_problems()
        return FolderPermissions()


class CombinedMixin(ProblemEditorMemberRequiredMixin, ProblemFolderMixin, FolderPermissionCheckMixin):
    pass


class ShowFolderView(CombinedMixin, IRunnerListView):
    template_name = 'problems/list_folder.html'
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query_string'] = make_folder_query_string(self.node.id)
        return context

    def get_queryset(self):
        return self.loader_cls.get_folder_content(self.request.user, self.node)


class CreateFolderView(CombinedMixin, generic.FormView):
    template_name = 'problems/list_folder_form.html'
    form_class = ProblemFolderForm
    requirements = FolderPermissions.MANAGE_FOLDERS
    needs_real_folder = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_name'] = _('Create folder')
        context['show_parent'] = True
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.parent_id = self.node.id
        obj.save()
        return redirect('problems:show_folder', FolderId.to_string(self.node.id))


class UpdateFolderView(CombinedMixin, generic.UpdateView):
    template_name = 'problems/list_folder_form.html'
    form_class = ProblemFolderForm
    requirements = FolderPermissions.MANAGE_FOLDERS
    needs_real_folder = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_name'] = _('Folder properties')
        context['show_parent'] = False
        return context

    def get_success_url(self):
        return reverse('problems:show_folder', kwargs={'folder_id_or_root': FolderId.to_string(self.node.id)})

    def get_object(self):
        return self.node.instance


class FolderAccessView(CombinedMixin, ShareFolderWithGroupMixin, generic.base.ContextMixin, generic.View):
    template_name = 'problems/list_folder_access.html'
    form_class = ProblemFolderForm
    requirements = FolderPermissions.VIEW_PROBLEMS
    requirements_to_post = FolderPermissions.GRANT_ACCESS
    access_model = ProblemFolderAccess
    needs_real_folder = True

    def get(self, request):
        context = self._get(request, self.node.instance)
        return render(request, self.template_name, self.get_context_data(**context))

    def post(self, request):
        success, context = self._post(request, self.node.instance)
        if success:
            return redirect('problems:folder_access', FolderId.to_string(self.node.id))
        return render(request, self.template_name, self.get_context_data(**context))


class DeleteFolderView(CombinedMixin, generic.base.ContextMixin, generic.View):
    template_name = 'problems/list_folder_confirm_delete.html'
    requirements = FolderPermissions.MANAGE_FOLDERS
    needs_real_folder = True

    def list_courses(self, folder):
        subfolder_ids = folder.get_descendants(include_self=True).values_list('id', flat=True)
        return list(Course.objects.filter(topic__problem_folder_id__in=subfolder_ids).distinct())

    def get(self, request):
        context = self.get_context_data(course_list=self.list_courses(self.node.instance))
        return render(request, self.template_name, context)

    def post(self, request):
        folder = self.node.instance
        parent_id = folder.parent_id
        with transaction.atomic():
            folder.delete()
        return redirect('problems:show_folder', FolderId.to_string(parent_id))


class ImportFromPolygonView(CombinedMixin, generic.base.ContextMixin, generic.View):
    template_name = 'problems/list_import_from_polygon.html'
    requirements = FolderPermissions.MANAGE_FOLDERS

    def get(self, request):
        # TODO: better way to select default compiler (remember last used?)
        compiler = Compiler.objects.filter(description__contains='GNU C++', default_for_courses=True).first()
        form = PolygonImportForm(initial={'compiler': compiler, 'language': settings.MODEL_LANGUAGES})

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request):
        form = PolygonImportForm(request.POST, request.FILES)
        has_error = False
        validation_error = None
        exception = None
        exception_type = None

        if form.is_valid():
            try:
                with transaction.atomic():
                    import_full_package(
                        form.cleaned_data['upload'],
                        form.cleaned_data['language'],
                        form.cleaned_data['compiler'],
                        request.user,
                        self.node.id
                    )
            except ValidationError as e:
                has_error = True
                validation_error = e
            except Exception as e:
                has_error = True
                exception = e
                exception_type = type(e).__name__

            if not has_error:
                return redirect('problems:show_folder', FolderId.to_string(self.node.id))

        context = self.get_context_data(form=form, has_error=has_error, validation_error=validation_error, exception=exception, exception_type=exception_type)
        return render(request, self.template_name, context)


class CreateProblemView(CombinedMixin, generic.FormView):
    template_name = 'problems/list_folder_form.html'
    form_class = SimpleProblemForm
    requirements = FolderPermissions.MANAGE_FOLDERS

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_name'] = _('New problem')
        context['show_parent'] = True
        return context

    def form_valid(self, form):
        with transaction.atomic():
            problem = form.save()
            if self.node.id is not None:
                problem.folders.add(self.node.id)

        url = reverse('problems:properties', kwargs={'problem_id': problem.id})
        url += make_folder_query_string(self.node.id)
        return HttpResponseRedirect(url)

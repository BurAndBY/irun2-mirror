import operator
from django.views import generic
import json
from django.contrib import auth
from django.shortcuts import get_object_or_404, render, render_to_response, redirect
import forms
from django.forms import formset_factory
from collections import namedtuple
from django.utils.translation import ugettext_lazy as _
from models import UserFolder, UserProfile
from common.folderutils import lookup_node_ex, cast_id
from common.views import IRunnerListView
from problems.models import Problem
from django.conf import settings
from django.contrib import auth
from django.db import transaction
from django.http import Http404
from django.db.models import Q


class IndexView(IRunnerListView):
    template_name = 'users/index.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['query'] = self.request.GET.get('query')
        context['active_tab'] = 'search'
        return context

    def get_queryset(self):
        queryset = auth.get_user_model().objects.all().select_related('userprofile').select_related('userprofile__folder')

        query = self.request.GET.get('query')
        if query:
            terms = query.split()
            if terms:
                search_args = []
                for term in terms:
                    for sql in ('username__icontains', 'first_name__icontains', 'last_name__icontains'):
                        search_args.append(Q(**{sql: term}))

                queryset = queryset.filter(reduce(operator.or_, search_args))
        queryset = queryset.order_by('id')
        return queryset


class UserFolderMixin(object):
    def get_context_data(self, **kwargs):
        context = super(UserFolderMixin, self).get_context_data(**kwargs)
        cached_trees = UserFolder.objects.all().get_cached_trees()
        node_ex = lookup_node_ex(self.kwargs['folder_id_or_root'], cached_trees)

        context['cached_trees'] = cached_trees
        context['folder'] = node_ex.object
        context['folder_id'] = node_ex.folder_id
        context['active_tab'] = 'folders'
        return context


class ShowFolderView(UserFolderMixin, IRunnerListView):
    template_name = 'users/folder.html'
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super(ShowFolderView, self).get_context_data(**kwargs)

        folder = context['folder']

        has_users = (self.get_queryset().count() > 0)
        can_delete_folder = (not has_users) and (folder is not None) and (folder.get_descendant_count() == 0)

        context['has_users'] = has_users
        context['can_delete_folder'] = can_delete_folder
        return context

    def get_queryset(self):
        folder_id = cast_id(self.kwargs['folder_id_or_root'])
        return auth.get_user_model().objects.filter(userprofile__folder_id=folder_id)


class CreateFolderView(UserFolderMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = forms.CreateFolderForm

    def get_context_data(self, **kwargs):
        context = super(CreateFolderView, self).get_context_data(**kwargs)
        context['form_name'] = _('Create folder')
        return context

    def form_valid(self, form):
        folder_id_or_root = self.kwargs['folder_id_or_root']
        folder_id = cast_id(folder_id_or_root)
        UserFolder.objects.create(name=form.cleaned_data['name'], parent_id=folder_id)
        return redirect('users:show_folder', folder_id_or_root)


class CreateUserView(UserFolderMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = forms.CreateUserForm

    def get_context_data(self, **kwargs):
        context = super(CreateUserView, self).get_context_data(**kwargs)
        context['form_name'] = _('Create user')
        return context

    def form_valid(self, form):
        folder_id_or_root = self.kwargs['folder_id_or_root']
        folder_id = cast_id(folder_id_or_root)
        with transaction.atomic():
            user = form.save()
            profile = user.userprofile
            profile.folder_id = folder_id
            profile.save()
        return redirect('users:show_folder', folder_id_or_root)


class CreateUsersMassView(UserFolderMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = forms.CreateUsersMassForm
    initial = {'password': '11111'}

    def get_context_data(self, **kwargs):
        context = super(CreateUsersMassView, self).get_context_data(**kwargs)
        context['form_name'] = _('Mass user registration')
        return context

    def form_valid(self, form):
        folder_id_or_root = self.kwargs['folder_id_or_root']
        folder_id = cast_id(folder_id_or_root)
        users = form.cleaned_data['tsv']
        with transaction.atomic():
            for user, userprofile in users:
                user.save()
                userprofile.user = user
                userprofile.folder_id = folder_id
                userprofile.save()
        return redirect('users:show_folder', folder_id_or_root)


class MassOperationView(generic.View):
    template_name = None
    form_class = None
    success_url = '/'

    @staticmethod
    def _make_int_list(ids):
        result = set()
        for x in ids:
            try:
                x = int(x)
            except:
                raise Http404('bad id')
            result.add(x)

        return list(result)

    def _make_context(self, query_dict, queryset):
        # take really existing ids
        ids = [object.pk for object in queryset]

        context = {
            'object_list': queryset,
            'ids': ids,
            'next': query_dict.get('next')
        }
        return context

    def _redirect(self):
        next = self.request.POST.get('next')
        if next is None:
            next = self.success_url
        return redirect(next)

    def get(self, request, *args, **kwargs):
        ids = MassOperationView._make_int_list(request.GET.getlist('id'))

        queryset = self.get_queryset().filter(pk__in=ids)

        context = self._make_context(request.GET, queryset)

        if self.form_class is not None:
            form = self.form_class()
            context['form'] = form

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        ids = MassOperationView._make_int_list(request.POST.getlist('id'))

        queryset = self.get_queryset().filter(pk__in=ids)

        if self.form_class is not None:
            form = self.form_class(request.POST)
            if form.is_valid():
                self.perform(queryset, form)
                return self._redirect()
            else:
                context = self._make_context(request.POST, queryset)
                context['form'] = form
                return render(request, self.template_name, context)

        self.perform(queryset, None)
        return self._redirect()

    '''
    Methods that may be overridden.
    '''
    def perform(self, queryset, form):
        # form is passed only if form_class is not None.
        # form is valid.
        raise NotImplementedError()

    def get_queryset(self):
        raise NotImplementedError()


class DeleteUsersView(MassOperationView):
    template_name = 'users/delete.html'

    def get_queryset(self):
        return auth.get_user_model().objects

    def perform(self, queryset, form):
        queryset.delete()


class MoveUsersView(MassOperationView):
    template_name = 'users/move.html'
    form_class = forms.MoveUsersForm

    def get_queryset(self):
        return UserProfile.objects.select_related('user')

    def perform(self, queryset, form):
        folder = form.cleaned_data['folder']
        queryset.update(folder=folder)

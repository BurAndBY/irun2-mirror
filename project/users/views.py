from django.views import generic
import json
from django.contrib import auth
from django.shortcuts import get_object_or_404, render, render_to_response, redirect
import forms
from django.forms import formset_factory
from collections import namedtuple
from django.utils.translation import ugettext_lazy as _
from models import UserFolder
from common.folderutils import lookup_node_ex, cast_id
from common.views import IRunnerListView
from problems.models import Problem
from django.conf import settings
from django.contrib import auth


class IndexView(generic.ListView):
    template_name = 'users/index.html'

    def get_queryset(self):
        return auth.get_user_model().objects.all()


class MassUserCreateView(generic.View):
    FormSet = formset_factory(forms.MassUserSingleForm, extra=0)

    @staticmethod
    def _parse_single(line):
        tokens = line.split()
        if len(tokens) >= 3:
            return {'username': tokens[0], 'first_name': tokens[2], 'last_name': tokens[1]}
        return None

    @staticmethod
    def _parse_all(tsv):
        result = []
        for line in tsv.split('\n'):
            line = line.strip()
            if line:
                parsed = MassUserCreateView._parse_single(line)
                if parsed is not None:
                    result.append(parsed)
        return result

    @staticmethod
    def _create_users(formset, password):
        result = []
        model = auth.get_user_model().objects
        for form in formset:
            cd = form.cleaned_data
            try:
                user = model.create_user(username=cd['username'],
                                         email=None,
                                         password=password,
                                         first_name=cd['first_name'],
                                         last_name=cd['last_name'])
                result.append(user)
            except:
                pass
        return result

    def get(self, request):
        form = forms.MassUserInitForm()
        context = {'form': form}
        return render(request, 'users/mass.html', context)

    def post(self, request):
        if 'init_button' in request.POST:
            initform = forms.MassUserInitForm(request.POST)
            if initform.is_valid():
                parsed = MassUserCreateView._parse_all(initform.cleaned_data['tsv'])
                if len(parsed) == 0:
                    context = {'users': []}
                    return render(request, 'users/mass_final.html', context)

                formset = MassUserCreateView.FormSet(initial=parsed)

                passwordform = forms.MassUserPasswordForm(initial={'password': '11111'})
                context = {'formset': formset, 'passwordform': passwordform}
                return render(request, 'users/mass_confirm.html', context)

        elif 'confirm_button' in request.POST:
            formset = MassUserCreateView.FormSet(request.POST)
            passwordform = forms.MassUserPasswordForm(request.POST)
            if formset.is_valid() and passwordform.is_valid():
                password = passwordform.cleaned_data['password']
                users = MassUserCreateView._create_users(formset, password)
                context = {'users': users}
                return render(request, 'users/mass_final.html', context)

        return redirect('users:mass_create')


class UserFolderMixin(object):
    def get_context_data(self, **kwargs):
        context = super(UserFolderMixin, self).get_context_data(**kwargs)
        cached_trees = UserFolder.objects.all().get_cached_trees()
        node_ex = lookup_node_ex(self.kwargs['folder_id_or_root'], cached_trees)

        context['cached_trees'] = cached_trees
        context['folder'] = node_ex.object
        context['folder_id'] = node_ex.folder_id
        return context


class ShowFolderView(UserFolderMixin, IRunnerListView):
    template_name = 'users/folder.html'
    paginate_by = 12

    def get_queryset(self):
        folder_id = cast_id(self.kwargs['folder_id_or_root'])
        return auth.get_user_model().objects.filter(userprofile__folder_id=folder_id)


class CreateFolderView(UserFolderMixin, generic.FormView):
    template_name = 'users/create_folder.html'
    form_class = forms.CreateFolderForm

    def form_valid(self, form):
        folder_id_or_root = self.kwargs['folder_id_or_root']
        folder_id = cast_id(folder_id_or_root)
        UserFolder.objects.create(name=form.cleaned_data['name'], parent_id=folder_id)
        return redirect('users:show_folder', folder_id_or_root)

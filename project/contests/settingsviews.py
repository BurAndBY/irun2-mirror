from collections import namedtuple

from django.contrib import auth
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _

from common.cacheutils import AllObjectsCache
from problems.models import Problem
from proglangs.models import Compiler
from storage.utils import store_with_metadata

from .forms import PropertiesForm, CompilersForm, ProblemsForm, StatementsForm, UsersForm
from .forms import TwoPanelProblemMultipleChoiceField, TwoPanelUserMultipleChoiceField
from .models import Membership, ContestProblem
from .views import BaseContestView


class ContestSettingsView(BaseContestView):
    tab = 'settings'

    def is_allowed(self, permissions):
        return permissions.settings


class PropertiesView(ContestSettingsView):
    subtab = 'properties'
    template_name = 'contests/settings_properties.html'

    def get(self, request, contest):
        form = PropertiesForm(instance=contest)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, contest):
        form = PropertiesForm(request.POST, instance=contest)
        if form.is_valid():
            form.save()
            return redirect('contests:settings_properties', contest_id=contest.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class DeleteView(ContestSettingsView):
    subtab = 'properties'
    template_name = 'contests/contest_confirm_delete.html'

    def get(self, request, contest):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, contest):
        contest.delete()
        return redirect('contests:index')


class CompilersView(ContestSettingsView):
    subtab = 'compilers'
    template_name = 'contests/settings_compilers.html'

    def get_context_data(self, **kwargs):
        context = super(CompilersView, self).get_context_data(**kwargs)
        context['compiler_cache'] = AllObjectsCache(Compiler)
        return context

    def get(self, request, contest):
        form = CompilersForm(instance=contest)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, contest):
        form = CompilersForm(request.POST, instance=contest)
        if form.is_valid():
            form.save()
            return redirect('contests:settings_compilers', contest_id=contest.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class ProblemsView(ContestSettingsView):
    subtab = 'problems'
    template_name = 'contests/settings_problems.html'

    def _make_form(self, contest, data=None):
        qs = contest.get_problems()
        form = ProblemsForm(data, initial={'problems': qs})
        form.fields['problems'].widget.url_params = [contest.id]
        if data is None:
            form.fields['problems'].queryset = qs
        return form

    def get(self, request, contest):
        form = self._make_form(contest)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, contest):
        form = self._make_form(contest, request.POST)

        if form.is_valid():
            objs = []
            for i, problem in enumerate(form.cleaned_data['problems']):
                objs.append(ContestProblem(contest=contest, problem=problem, ordinal_number=i+1))

            with transaction.atomic():
                ContestProblem.objects.filter(contest=contest).delete()
                ContestProblem.objects.bulk_create(objs)

            return redirect('contests:settings_problems', contest_id=contest.id)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class ProblemsJsonListView(ContestSettingsView):
    def get(self, request, course, folder_id):
        problems = Problem.objects.filter(folders__id=folder_id)
        return TwoPanelProblemMultipleChoiceField.ajax(problems)


class FakeFile(object):
    def __init__(self, contest_id, filename):
        self.url = reverse('contests:statements', kwargs={'contest_id': contest_id, 'filename': filename})
        self.name = filename

    def __unicode__(self):
        return self.name


class StatementsView(ContestSettingsView):
    subtab = 'statements'
    template_name = 'contests/settings_statements.html'

    def _make_form(self, contest, data=None, files=None):
        if contest.statements is not None:
            f = FakeFile(contest.id, contest.statements.filename)
        else:
            f = None
        form = StatementsForm(data=data, files=files, initial={'upload': f})
        return form

    def get(self, request, contest):
        form = self._make_form(contest)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, contest):
        form = self._make_form(contest, request.POST, request.FILES)
        if form.is_valid():
            upload = form.cleaned_data['upload']

            if not upload:
                contest.statements = None
                contest.save()
            elif type(upload) is FakeFile:
                # do not change existing file
                pass
            else:
                contest.statements = store_with_metadata(upload)
                contest.save()

            return redirect('contests:settings_statements', contest_id=contest.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


UserFormPair = namedtuple('UserFormPair', 'user form')
RoleUsersViewModel = namedtuple('RoleUsersViewModel', 'name_plural tag users')

TAG_TO_NAME = {
    'contestants': _('Contestants'),
    'jury': _('Jury'),
}
TAG_TO_ROLE = {
    'contestants': Membership.CONTESTANT,
    'jury': Membership.JUROR,
}


class UsersView(ContestSettingsView):
    subtab = 'users'
    template_name = 'contests/settings_users.html'

    def _make_view_model(self, tag):
        role = TAG_TO_ROLE[tag]
        queryset = Membership.objects.filter(contest=self.contest, role=role).select_related('user')
        users = [membership.user for membership in queryset]
        return RoleUsersViewModel(TAG_TO_NAME[tag], tag, users)

    def _make_view_models(self, data=None):
        return [
            self._make_view_model('contestants'),
            self._make_view_model('jury'),
        ]

    def get(self, request, contest):
        view_models = self._make_view_models()
        context = self.get_context_data(view_models=view_models)
        return render(request, self.template_name, context)


class UserRoleView(ContestSettingsView):
    subtab = 'users'
    template_name = 'contests/settings_users_edit.html'

    def _list_users(self, contest, role):
        return contest.members.filter(contestmembership__role=role)

    @staticmethod
    def _parse_role(tag):
        role = TAG_TO_ROLE.get(tag)
        if role is None:
            raise Http404('unknown role')
        return role

    def _make_form(self, contest, present_users, data=None):
        form = UsersForm(data, initial={'users': present_users})
        form.fields['users'].widget.url_params = [contest.id]
        return form

    def get(self, request, contest, tag):
        role = self._parse_role(tag)
        present_users = self._list_users(contest, role)
        form = self._make_form(contest, present_users)

        context = self.get_context_data(form=form, name_plural=TAG_TO_NAME[tag])
        return render(request, self.template_name, context)

    def post(self, request, contest, tag):
        role = self._parse_role(tag)
        present_users = self._list_users(contest, role)
        form = self._make_form(contest, present_users, request.POST)

        if form.is_valid():
            present_ids = set(user.id for user in present_users)
            target_users = form.cleaned_data['users']
            target_ids = set(user.id for user in target_users)
            with transaction.atomic():
                for user in present_users:
                    if user.id not in target_ids:
                        Membership.objects.filter(role=role, contest=contest, user=user).delete()
                for user in target_users:
                    if user.id not in present_ids:
                        Membership.objects.create(role=role, contest=contest, user=user)

            return redirect('contests:settings_users', contest.id)

        context = self.get_context_data(form=form, name_plural=TAG_TO_NAME[tag])
        return render(request, self.template_name, context)


class UsersJsonListView(ContestSettingsView):
    def get(self, request, contest, folder_id):
        users = auth.get_user_model().objects.filter(userprofile__folder_id=folder_id)
        return TwoPanelUserMultipleChoiceField.ajax(users)

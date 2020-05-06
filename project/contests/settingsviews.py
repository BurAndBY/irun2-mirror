from collections import namedtuple

from django.contrib import auth
from django.urls import reverse
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from common.cacheutils import AllObjectsCache
from common.tree.fields import FOLDER_ID_PLACEHOLDER
from common.tree.key import folder_id_or_404
from common.bulk.update import change_rowset_3p, notify_users_changed
from problems.models import Problem
from proglangs.models import Compiler
from storage.utils import store_with_metadata

from .forms import PropertiesForm, AccessForm, LimitsForm, CompilersForm
from .forms import ProblemsForm, StatementsForm, UsersForm, PrintingForm, UserFilterForm
from .forms import ThreePanelProblemMultipleChoiceField, ThreePanelUserMultipleChoiceField
from .models import Contest, Membership, ContestProblem, UserFilter
from .views import BaseContestView


class ContestSettingsView(BaseContestView):
    tab = 'settings'

    def is_allowed(self, permissions):
        return permissions.settings


class SingleFormView(ContestSettingsView):
    template_name = 'contests/settings_properties.html'
    form_class = None
    url_pattern = None
    can_delete = False

    def get_context_data(self, **kwargs):
        context = super(SingleFormView, self).get_context_data(**kwargs)
        context['can_delete'] = self.can_delete
        return context

    def get(self, request, contest):
        form = self.form_class(instance=contest)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, contest):
        form = self.form_class(request.POST, instance=contest)
        if form.is_valid():
            form.save()
            return redirect(self.url_pattern, contest_id=contest.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class PropertiesView(SingleFormView):
    form_class = PropertiesForm
    subtab = 'properties'
    url_pattern = 'contests:settings_properties'
    can_delete = True


class AccessView(SingleFormView):
    form_class = AccessForm
    subtab = 'access'
    url_pattern = 'contests:settings_access'


class LimitsView(SingleFormView):
    form_class = LimitsForm
    subtab = 'limits'
    url_pattern = 'contests:settings_limits'


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
        form = ProblemsForm(data)
        form.fields['problems'].configure(
            initial=contest.get_problems(),
            user=self.request.user,
            url_template=reverse('contests:settings_problems_json_list', args=(contest.id, FOLDER_ID_PLACEHOLDER))
        )
        return form

    def get(self, request, contest):
        form = self._make_form(contest)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, contest):
        form = self._make_form(contest, request.POST)

        if form.is_valid():
            objs = []
            for i, problem_id in enumerate(form.cleaned_data['problems'].pks):
                objs.append(ContestProblem(contest=contest, problem_id=problem_id, ordinal_number=i+1))

            with transaction.atomic():
                ContestProblem.objects.filter(contest=contest).delete()
                ContestProblem.objects.bulk_create(objs)

            return redirect('contests:settings_problems', contest_id=contest.id)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class ProblemsJsonListView(ContestSettingsView):
    def get(self, request, contest, folder_id):
        return ThreePanelProblemMultipleChoiceField.ajax(request.user, folder_id)


@python_2_unicode_compatible
class FakeFile(object):
    def __init__(self, contest_id, filename):
        self.url = reverse('contests:statements', kwargs={'contest_id': contest_id, 'filename': filename})
        self.name = filename

    def __str__(self):
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
RoleUsersViewModel = namedtuple('RoleUsersViewModel', 'name_plural tag users enable_filters')

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
        enable_filters = (role == Membership.CONTESTANT)
        return RoleUsersViewModel(TAG_TO_NAME[tag], tag, users, enable_filters)

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
        form = UsersForm(data)
        form.fields['users'].configure(
            initial=present_users,
            user=self.request.user,
            url_template=reverse('contests:settings_users_json_list', args=(contest.id, FOLDER_ID_PLACEHOLDER))
        )
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
            with transaction.atomic():
                diff = change_rowset_3p(form.cleaned_data['users'], Membership, 'user_id', {'role': role, 'contest': contest})
            notify_users_changed(request, diff)
            return redirect('contests:settings_users', contest.id)

        context = self.get_context_data(form=form, name_plural=TAG_TO_NAME[tag])
        return render(request, self.template_name, context)


class UsersJsonListView(ContestSettingsView):
    def get(self, request, contest, folder_id):
        return ThreePanelUserMultipleChoiceField.ajax(request.user, folder_id)


class UsersFilterVew(ContestSettingsView):
    subtab = 'users'
    template_name = 'contests/settings_filter.html'

    def _make_formset_class(self):
        return inlineformset_factory(Contest, UserFilter, form=UserFilterForm, fields=('name', 'regex'), can_delete=True, extra=1)

    def get(self, request, contest):
        FilterFormSet = self._make_formset_class()
        formset = FilterFormSet(instance=contest)
        context = self.get_context_data(formset=formset)
        return render(request, self.template_name, context)

    def post(self, request, contest):
        FilterFormSet = self._make_formset_class()
        formset = FilterFormSet(request.POST, instance=contest)
        if formset.is_valid():
            with transaction.atomic():
                formset.save()
            return redirect('contests:settings_filters', contest.id)
        context = self.get_context_data(formset=formset)
        return render(request, self.template_name, context)


class PrintingView(SingleFormView):
    form_class = PrintingForm
    subtab = 'printing'
    url_pattern = 'contests:settings_printing'

from django.db import transaction
from django.shortcuts import render, redirect
from django.views import generic
from django.utils.translation import ugettext_lazy as _

from cauth.mixins import LoginRequiredMixin, StaffMemberRequiredMixin
from proglangs.models import Compiler
from .models import Contest, UnauthorizedAccessLevel
from collections import namedtuple

ContestInfo = namedtuple('ContestInfo', 'contest is_private')


class ContestSet(object):
    ALL = 1
    MY = 2
    PUBLIC = 3
    MY_AND_PUBLIC = 4


def _get_page_title(cs):
    if cs == ContestSet.ALL:
        return _('All contests')
    if cs == ContestSet.MY:
        return _('My contests')
    return _('Contests')


def _fetch_contests(cs, user):
    contests = Contest.objects
    if cs == ContestSet.ALL:
        return contests

    if cs == ContestSet.MY:
        return contests.filter(membership__user=user)
    if cs == ContestSet.PUBLIC:
        return contests.exclude(unauthorized_access=UnauthorizedAccessLevel.NO_ACCESS)
    if cs == ContestSet.MY_AND_PUBLIC:
        my_contests = contests.filter(membership__user=user)
        public_contests = contests.exclude(unauthorized_access=UnauthorizedAccessLevel.NO_ACCESS)
        return (my_contests | public_contests).distinct()


def _make_contest_list_data(contests):
    year_to_contests = {}
    for contest in contests.order_by('-start_time'):
        year = contest.start_time.year
        is_private = contest.unauthorized_access == UnauthorizedAccessLevel.NO_ACCESS
        year_to_contests.setdefault(year, []).append(ContestInfo(contest, is_private))

    pairs = year_to_contests.items()
    pairs.sort(reverse=True)
    return pairs


def _get_allowed_contest_set(user):
    if not user.is_authenticated():
        return ContestSet.PUBLIC
    if not user.is_staff:
        return ContestSet.MY_AND_PUBLIC
    return ContestSet.ALL


def _make_context(cs, user):
    return {
        'pairs': _make_contest_list_data(_fetch_contests(cs, user)),
        'page_title': _get_page_title(cs),
        'may_create_contests': cs == ContestSet.ALL,
        'enable_my': user.is_authenticated(),
    }


class ContestListView(generic.View):
    model = Contest
    template_name = 'contests/contest_list.html'

    def get(self, request):
        context = _make_context(_get_allowed_contest_set(request.user), request.user)
        return render(request, self.template_name, context)


class MyContestListView(LoginRequiredMixin, generic.View):
    model = Contest
    template_name = 'contests/contest_list.html'

    def get(self, request):
        context = _make_context(ContestSet.MY, request.user)
        return render(request, self.template_name, context)


class ContestCreateView(StaffMemberRequiredMixin, generic.CreateView):
    model = Contest
    fields = ['name', 'rules', 'kind', 'start_time', 'duration', 'freeze_time']

    def form_valid(self, form):
        with transaction.atomic():
            contest = form.save(commit=True)
            contest.compilers = Compiler.objects.filter(default_for_contests=True)
        return redirect('contests:settings_properties', contest.id)

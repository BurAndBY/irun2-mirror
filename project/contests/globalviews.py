from django.db import transaction
from django.shortcuts import render, redirect
from django.views import generic

from cauth.mixins import StaffMemberRequiredMixin
from proglangs.models import Compiler

from .models import Contest


class ContestListView(StaffMemberRequiredMixin, generic.View):
    model = Contest
    template_name = 'contests/contest_list.html'

    def get(self, request):
        year_to_contests = {}
        for contest in Contest.objects.order_by('-start_time'):
            year = contest.start_time.year
            year_to_contests.setdefault(year, []).append(contest)

        pairs = year_to_contests.items()
        pairs.sort(reverse=True)

        return render(request, self.template_name, {'pairs': pairs})


class ContestCreateView(StaffMemberRequiredMixin, generic.CreateView):
    model = Contest
    fields = ['name', 'start_time', 'duration', 'freeze_time']

    def form_valid(self, form):
        with transaction.atomic():
            contest = form.save(commit=True)
            contest.compilers = Compiler.objects.filter(legacy=False)
        return redirect('contests:settings_properties', contest.id)

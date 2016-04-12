from django.db import transaction
from django.shortcuts import redirect
from django.views import generic

from cauth.mixins import StaffMemberRequiredMixin
from proglangs.models import Compiler

from .models import Contest


class ContestListView(StaffMemberRequiredMixin, generic.ListView):
    model = Contest
    template_name = 'contests/contest_list.html'


class ContestCreateView(StaffMemberRequiredMixin, generic.CreateView):
    model = Contest
    fields = ['name', 'start_time', 'duration', 'freeze_time']

    def form_valid(self, form):
        with transaction.atomic():
            contest = form.save(commit=True)
            contest.compilers = Compiler.objects.filter(legacy=False)
        return redirect('contests:settings_properties', contest.id)

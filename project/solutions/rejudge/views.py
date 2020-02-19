from collections import namedtuple

from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.translation import pgettext_lazy
from django.views import generic

from cauth.mixins import StaffMemberRequiredMixin
from common.outcome import Outcome
from common.pagination.views import IRunnerListView
from common.views import MassOperationView
from problems.models import Problem

from solutions.models import Solution, Judgement, Rejudge
from solutions.utils import bulk_rejudge


class RejudgeListView(StaffMemberRequiredMixin, IRunnerListView):
    template_name = 'solutions/rejudge/rejudge_list.html'

    def get_queryset(self):
        return Rejudge.objects.all().annotate(num_judgements=Count('judgement')).order_by('-creation_time', '-id')


class CreateRejudgeView(StaffMemberRequiredMixin, MassOperationView):
    template_name = 'solutions/confirm_multiple.html'

    def get_context_data(self, **kwargs):
        context = super(CreateRejudgeView, self).get_context_data(**kwargs)
        context['action'] = pgettext_lazy('verb', 'rejudge')
        return context

    def perform(self, filtered_queryset, form):
        with transaction.atomic():
            notifier, rejudge = bulk_rejudge(filtered_queryset, self.request.user)
        notifier.notify()
        return redirect('solutions:rejudge', rejudge.id)

    def get_queryset(self):
        return Solution.objects.order_by('id')


RejudgeInfo = namedtuple('RejudgeInfo', ['solution', 'before', 'after', 'current'])
RejudgeStats = namedtuple('RejudgeStats', ['total', 'accepted', 'rejected'])


def fetch_rejudge_stats(rejudge_id):
    queryset = Judgement.objects.filter(rejudge_id=rejudge_id)
    total = queryset.count()
    accepted = queryset.filter(status=Judgement.DONE).filter(outcome=Outcome.ACCEPTED).count()
    rejected = queryset.filter(status=Judgement.DONE).exclude(outcome=Outcome.ACCEPTED).count()
    return RejudgeStats(total, accepted, rejected)


class RejudgeView(StaffMemberRequiredMixin, generic.View):
    template_name = 'solutions/rejudge/rejudge.html'

    def get(self, request, rejudge_id):
        rejudge = get_object_or_404(Rejudge, pk=rejudge_id)
        object_list = []
        problem_ids = set()

        for new_judgement in rejudge.judgement_set.all().\
                select_related('solution').\
                select_related('judgement_before').\
                select_related('solution__best_judgement').\
                select_related('solution__author').\
                select_related('solution__source_code').\
                prefetch_related('solution__compiler'):
            solution = new_judgement.solution

            problem_ids.add(solution.problem_id)

            before = new_judgement.judgement_before
            after = new_judgement
            current = solution.best_judgement
            object_list.append(RejudgeInfo(solution, before, after, current))

        problem = None
        if len(problem_ids) == 1:
            problem = Problem.objects.get(pk=next(iter(problem_ids)))

        progress_url = reverse('solutions:rejudge_status_json', kwargs={'rejudge_id': rejudge_id})
        context = {
            'rejudge': rejudge,
            'object_list': object_list,
            'progress_url': progress_url,
            'stats': fetch_rejudge_stats(rejudge_id),
            'problem': problem,
        }
        return render(request, self.template_name, context)

    def post(self, request, rejudge_id):
        need_commit = ('commit' in request.POST)
        need_rollback = ('rollback' in request.POST)
        need_clone = ('clone' in request.POST)
        if need_clone:
            with transaction.atomic():
                notifier, rejudge = bulk_rejudge(Solution.objects.filter(judgement__rejudge_id=rejudge_id), self.request.user)
            notifier.notify()
            return redirect('solutions:rejudge', rejudge.id)

        if (need_commit ^ need_rollback):
            target = True if need_commit else False
            num_rows = Rejudge.objects.filter(id=rejudge_id, committed=None).update(committed=target)
            if num_rows and need_commit:
                with transaction.atomic():
                    rejudge = get_object_or_404(Rejudge, pk=rejudge_id)
                    for new_judgement in rejudge.judgement_set.all().select_related('solution'):
                        solution = new_judgement.solution
                        solution.best_judgement = new_judgement
                        solution.save()

        return redirect('solutions:rejudge', rejudge_id)


class RejudgeJsonView(StaffMemberRequiredMixin, generic.View):
    def get(self, request, rejudge_id):
        stats = fetch_rejudge_stats(rejudge_id)
        return JsonResponse({
            'total': stats.total,
            'valueGood': stats.accepted,
            'valueBad': stats.rejected,
        })

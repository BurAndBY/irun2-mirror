import difflib
from collections import namedtuple

from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import ugettext_lazy, pgettext_lazy
from django.views import generic

from cauth.mixins import LoginRequiredMixin, StaffMemberRequiredMixin
from common.outcome import Outcome
from common.pageutils import paginate
from common.views import MassOperationView, IRunnerListView
from problems.models import Problem

from .compare import fetch_solution
from .filters import apply_state_filter, apply_compiler_filter, apply_difficulty_filter
from .forms import AllSolutionsFilterForm, CompareSolutionsForm
from .models import Solution, Judgement, Rejudge, Challenge
from .utils import bulk_rejudge


'''
All solutions list
'''


class SolutionListView(StaffMemberRequiredMixin, generic.View):
    paginate_by = 25
    template_name = 'solutions/solution_list.html'

    def get(self, request):
        form = AllSolutionsFilterForm(request.GET)

        queryset = Solution.objects.\
            prefetch_related('compiler').\
            prefetch_related('problem').\
            prefetch_related('author').\
            select_related('best_judgement').\
            select_related('source_code').\
            prefetch_related('aggregatedresult').\
            defer('ip_address', 'source_code__resource_id').\
            order_by('-id')

        if form.is_valid():
            queryset = apply_state_filter(queryset, form.cleaned_data['state'])
            queryset = apply_compiler_filter(queryset, form.cleaned_data['compiler'])

            user_id = form.cleaned_data.get('user')
            if user_id is not None:
                queryset = queryset.filter(author_id=user_id)

            problem_id = form.cleaned_data.get('problem')
            if problem_id is not None:
                queryset = queryset.filter(problem_id=problem_id)

            difficulty = form.cleaned_data.get('difficulty')
            if difficulty is not None:
                queryset = apply_difficulty_filter(queryset, difficulty)

        context = paginate(request, queryset, self.paginate_by, allow_all=False)
        context['form'] = form
        return render(request, self.template_name, context)


'''
Judgement
'''


class JudgementListView(StaffMemberRequiredMixin, generic.View):
    paginate_by = 25
    template_name = 'solutions/judgement_list.html'

    def get(self, request):
        queryset = Judgement.objects.select_related('extra_info').order_by('-id')
        context = paginate(request, queryset, self.paginate_by, allow_all=False)
        return render(request, self.template_name, context)


'''
Rejudge
'''


class RejudgeListView(StaffMemberRequiredMixin, IRunnerListView):
    template_name = 'solutions/rejudge_list.html'

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
    template_name = 'solutions/rejudge.html'

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


'''
Mass delete
'''


class DeleteSolutionsView(StaffMemberRequiredMixin, MassOperationView):
    template_name = 'solutions/confirm_multiple.html'

    def get_context_data(self, **kwargs):
        context = super(DeleteSolutionsView, self).get_context_data(**kwargs)
        context['action'] = ugettext_lazy('delete')
        return context

    def perform(self, filtered_queryset, form):
        filtered_queryset.delete()

    def get_queryset(self):
        return Solution.objects.order_by('id')


'''
Compare two solutions
'''


class CompareSolutionsView(LoginRequiredMixin, generic.View):
    template_name = 'solutions/compare.html'

    def _get_compare_context(self, first_id, second_id, contextual_diff):
        first = fetch_solution(first_id, self.request.user)
        second = fetch_solution(second_id, self.request.user)
        ok = (first.text is not None) and (second.text is not None)
        context = {}
        context['first'] = first
        context['second'] = second
        context['has_error'] = not ok
        context['has_result'] = ok
        context['show_author'] = (first.solution.author_id != second.solution.author_id) if (first.solution is not None and second.solution is not None) else False
        context['full'] = not contextual_diff

        if ok:
            first_lines = first.text.splitlines()
            second_lines = second.text.splitlines()
            differ = difflib.HtmlDiff(tabsize=4, wrapcolumn=None)
            html = differ.make_table(first_lines, second_lines, context=contextual_diff)
            html = html.replace('<td nowrap="nowrap">', '<td>')
            html = html.replace('&nbsp;', ' ')
            context['difflib_html_content'] = html

        return context

    def get(self, request):
        if request.GET:
            form = CompareSolutionsForm(request.GET)
            if form.is_valid():
                context = self._get_compare_context(form.cleaned_data['first'], form.cleaned_data['second'], form.cleaned_data['diff'])
                return render(request, self.template_name, context)
        else:
            form = CompareSolutionsForm()

        # fallback
        context = {'form': form}
        return render(request, self.template_name, context)


'''
Global challenges list
'''


class ChallengeListView(StaffMemberRequiredMixin, IRunnerListView):
    template_name = 'solutions/challenge_list.html'

    def get_queryset(self):
        return Challenge.objects.\
            annotate(num_solutions=Count('challengedsolution')).\
            select_related('problem').\
            order_by('-creation_time', '-id').\
            all()

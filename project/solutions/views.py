import difflib

from django.db.models import Count
from django.shortcuts import render
from django.utils.translation import ugettext_lazy
from django.views import generic

from cauth.mixins import StaffMemberRequiredMixin, ProblemEditorMemberRequiredMixin
from common.pagination import paginate
from common.pagination.views import IRunnerListView
from common.views import MassOperationView
from problems.calcpermissions import get_problem_ids_queryset, has_limited_problems_queryset

from .compare import fetch_solution
from .filters import apply_state_filter, apply_compiler_filter, apply_difficulty_filter
from .forms import AllSolutionsFilterForm, CompareSolutionsForm
from .models import Solution, Judgement, Challenge


'''
All solutions list
'''


class SolutionListView(ProblemEditorMemberRequiredMixin, generic.View):
    paginate_by = 25
    template_name = 'solutions/solution_list.html'

    def get(self, request):
        form = AllSolutionsFilterForm(request.GET)

        queryset = Solution.objects.\
            prefetch_related('compiler').\
            prefetch_related('problem').\
            prefetch_related('author').\
            select_related('best_judgement').\
            prefetch_related('source_code').\
            prefetch_related('aggregatedresult').\
            defer('ip_address', 'stop_on_fail', 'source_code__resource_id', 'best_judgement__rejudge_id', 'best_judgement__judgement_before_id').\
            order_by('-id')

        if has_limited_problems_queryset(request.user):
            queryset = queryset.filter(problem_id__in=get_problem_ids_queryset(request.user))

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

        context = paginate(request, queryset, self.paginate_by, allow_all=False, show_total_count=request.user.is_staff)
        context['form'] = form
        return render(request, self.template_name, context)


'''
Judgement
'''


class JudgementListView(ProblemEditorMemberRequiredMixin, generic.View):
    paginate_by = 25
    template_name = 'solutions/judgement_list.html'

    def get(self, request):
        queryset = Judgement.objects.prefetch_related('extra_info').order_by('-id')
        if has_limited_problems_queryset(request.user):
            queryset = queryset.filter(solution__problem_id__in=get_problem_ids_queryset(request.user))

        context = paginate(request, queryset, self.paginate_by, allow_all=True, show_total_count=request.user.is_staff)
        return render(request, self.template_name, context)


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


class CompareSolutionsView(ProblemEditorMemberRequiredMixin, generic.View):
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


class ChallengeListView(ProblemEditorMemberRequiredMixin, IRunnerListView):
    template_name = 'solutions/challenge_list.html'

    def get_queryset(self):
        qs = Challenge.objects.\
            annotate(num_solutions=Count('challengedsolution')).\
            select_related('problem').\
            order_by('-creation_time', '-id').\
            all()
        if has_limited_problems_queryset(self.request.user):
            qs = qs.filter(problem_id__in=get_problem_ids_queryset(self.request.user))
        return qs

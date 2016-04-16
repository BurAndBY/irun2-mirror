from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.views import generic
from django.utils.translation import pgettext
from django.utils import timezone

from common.pageutils import paginate
from problems.models import Problem
from problems.views import ProblemStatementMixin
from solutions.models import Solution
from solutions.utils import new_solution, judge
from storage.utils import serve_resource_metadata
from users.models import UserProfile

from .calcpermissions import calculate_contest_permissions
from .forms import SolutionListUserForm, SolutionListProblemForm, ContestSolutionForm, MessageForm
from .models import Contest, Membership, ContestSolution, Message, MessageUser
from .services import make_contestant_choices, make_problem_choices, make_contest_results, make_letter
from .services import ProblemResolver, ContestTiming


class BaseContestView(generic.View):
    tab = None
    subtab = None

    def __init__(self, *args, **kwargs):
        super(BaseContestView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {
            'contest': self.contest,
            'timing': self.timing,
            'permissions': self.permissions,
            'active_tab': self.tab,
            'active_subtab': self.subtab,
        }
        self._fill_unread_counters(context)
        context.update(kwargs)
        return context

    def _fill_unread_counters(self, context):
        me = self.request.user
        if not me.is_authenticated():
            return

        if self.permissions.read_messages or self.permissions.manage_messages:
            qs = Message.objects.filter(contest=self.contest, message_type=Message.MESSAGE)
            if not self.permissions.manage_messages:
                qs = qs.filter(Q(recipient=me) | Q(recipient__isnull=True))

            # TODO: less queries?
            all_count = qs.count()
            read_count = qs.filter(messageuser__user=me).count()
            context['unread_messages'] = all_count - read_count

    def is_allowed(self, permissions):
        return False

    def dispatch(self, request, contest_id, *args, **kwargs):
        self.contest = get_object_or_404(Contest, pk=contest_id)
        self.timing = ContestTiming(self.contest)
        if request.user.is_authenticated():
            self.permissions = calculate_contest_permissions(self.contest, request.user, Membership.objects.filter(contest_id=contest_id, user=request.user))
        else:
            self.permissions = calculate_contest_permissions(self.contest, None, [])

        if not self.is_allowed(self.permissions):
            raise PermissionDenied()
        return super(BaseContestView, self).dispatch(request, self.contest, *args, **kwargs)


class GeneralView(BaseContestView):
    def is_allowed(self, permissions):
        return permissions.standings

    def get(self, request, contest):
        return redirect('contests:standings', contest.id)


class StandingsView(BaseContestView):
    tab = 'standings'
    wide = False

    def is_allowed(self, permissions):
        return permissions.standings

    def are_standings_available(self):
        if self.timing.get() == ContestTiming.BEFORE:
            return self.permissions.standings_before
        return True

    def get(self, request, contest):
        if self.are_standings_available():
            # Do not show standings before the contest because they contain names of problems!
            frozen = (self.timing.is_freeze_applicable()) and (not self.permissions.always_unfrozen_standings)
            contest_results = make_contest_results(contest, frozen=frozen)

            # privileged users may click on contestants to see their solutions
            user_url = reverse('contests:all_solutions', kwargs={'contest_id': contest.id}) if self.permissions.all_solutions else None
            my_id = request.user.id if request.user.is_authenticated() else None

            context = self.get_context_data(results=contest_results, my_id=my_id, user_url=user_url)
        else:
            context = self.get_context_data()

        template_name = 'contests/standings.html' if not self.wide else 'contests/standings_wide.html'
        return render(request, template_name, context)


class ContestProblemsetMixin(object):
    template_name_later = 'contests/problems_later.html'

    def is_problemset_available(self):
        if self.timing.get() == ContestTiming.BEFORE:
            return self.permissions.problems_before
        return True

    def later(self, request):
        context = self.get_context_data()
        return render(request, self.template_name_later, context)


class StatementsFileView(ContestProblemsetMixin, BaseContestView):
    tab = 'problems'

    def is_allowed(self, permissions):
        return permissions.problems

    def get(self, request, contest, filename):
        if not self.is_problemset_available():
            return self.later(request)

        return serve_resource_metadata(request, contest.statements, force_download=False)


class ProblemsView(ContestProblemsetMixin, BaseContestView):
    tab = 'problems'
    template_name = 'contests/problems_list.html'

    def is_allowed(self, permissions):
        return permissions.problems

    def get(self, request, contest):
        if not self.is_problemset_available():
            return self.later(request)

        problems = [(make_letter(i), problem) for i, problem in enumerate(contest.get_problems())]
        context = self.get_context_data(statements=contest.statements, problems=problems)
        return render(request, self.template_name, context)


class ProblemView(ProblemStatementMixin, ContestProblemsetMixin, BaseContestView):
    tab = 'problems'
    template_name = 'contests/problem.html'

    def is_allowed(self, permissions):
        return permissions.problems

    def get(self, request, contest, problem_id, filename):
        if not self.is_problemset_available():
            return self.later(request)

        problem = Problem.objects.filter(pk=problem_id, link_to_contest__contest=self.contest).first()
        if problem is None:
            return redirect('contests:problems', contest.id)

        if self.is_aux_file(filename):
            return self.serve_aux_file(request, problem.id, filename)

        context = self.get_context_data()
        context['problem'] = problem
        context['statement'] = self.make_statement(problem)
        context['problem_to_submit'] = problem.id
        return render(request, self.template_name, context)


class AllSolutionsView(BaseContestView):
    tab = 'all_solutions'
    template_name = 'contests/all_solutions.html'
    paginate_by = 25

    def is_allowed(self, permissions):
        return permissions.all_solutions

    def get(self, request, contest):
        solutions = Solution.objects.all()\
            .filter(contestsolution__contest=contest)\
            .prefetch_related('compiler')\
            .select_related('source_code', 'best_judgement', 'author')\
            .order_by('-reception_time', 'id')

        user_form = SolutionListUserForm(data=request.GET, user_choices=make_contestant_choices(contest))
        if user_form.is_valid():
            solutions = solutions.filter(author_id=user_form.cleaned_data['user'])

        problem_form = SolutionListProblemForm(data=request.GET, problem_choices=make_problem_choices(contest))
        if problem_form.is_valid():
            solutions = solutions.filter(problem_id=problem_form.cleaned_data['problem'])

        context = paginate(request, solutions, self.paginate_by)

        context['user_form'] = user_form
        context['problem_form'] = problem_form
        context['resolver'] = ProblemResolver(contest)

        context = self.get_context_data(**context)
        return render(request, self.template_name, context)


class MySolutionsView(BaseContestView):
    tab = 'my_solutions'
    template_name = 'contests/my_solutions.html'
    paginate_by = 25

    def is_allowed(self, permissions):
        return permissions.my_solutions

    def get(self, request, contest):
        solutions = Solution.objects.all()\
            .filter(contestsolution__contest=contest, author=request.user)\
            .prefetch_related('compiler')\
            .select_related('source_code', 'best_judgement')\
            .order_by('-reception_time', 'id')

        problem_form = SolutionListProblemForm(data=request.GET, problem_choices=make_problem_choices(contest))
        if problem_form.is_valid():
            solutions = solutions.filter(problem_id=problem_form.cleaned_data['problem'])

        context = paginate(request, solutions, self.paginate_by)

        context['problem_form'] = problem_form
        context['resolver'] = ProblemResolver(contest)

        context = self.get_context_data(**context)
        return render(request, self.template_name, context)


class SubmitView(BaseContestView):
    tab = 'submit'
    template_name = 'contests/submit.html'

    def is_allowed(self, permissions):
        return permissions.submit

    def _make_initial(self):
        initial = {}

        problem_id = self.request.GET.get('problem')
        if problem_id is not None:
            try:
                problem_id = int(problem_id)
            except (TypeError, ValueError):
                problem_id = None

        if problem_id is not None:
            initial['problem'] = problem_id

        last_used_compiler = self.request.user.userprofile.last_used_compiler
        if last_used_compiler is not None:
            initial['compiler'] = last_used_compiler

        return initial

    def _make_form(self, data=None, files=None):
        form = ContestSolutionForm(
            data=data,
            files=files,
            problem_choices=make_problem_choices(self.contest),
            compiler_queryset=self.contest.compilers,
            initial=self._make_initial(),
            file_size_limit=self.contest.file_size_limit,
        )
        return form

    def _get_status(self):
        if self.permissions.submit_always:
            return (True, '')
        if self.timing.get() == ContestTiming.BEFORE:
            return (False, 'BEFORE')
        if self.timing.get() == ContestTiming.IN_PROGRESS:
            return (True, '')
        if self.timing.get() == ContestTiming.AFTER:
            if self.contest.enable_upsolving:
                return (True, 'UPSOLVING')
            else:
                return (False, 'AFTER')
        return (False, '')

    def get(self, request, contest):
        enable, status = self._get_status()
        form = self._make_form() if enable else None
        context = self.get_context_data(form=form, status=status)
        return render(request, self.template_name, context)

    def post(self, request, contest):
        enable, status = self._get_status()
        if enable:
            form = self._make_form(request.POST, request.FILES)
            if form.is_valid():
                with transaction.atomic():
                    # remember used compiler to select it again later
                    UserProfile.objects.filter(pk=request.user.id).update(last_used_compiler=form.cleaned_data['compiler'])

                    solution = new_solution(request, form, problem_id=form.cleaned_data['problem'])
                    ContestSolution.objects.create(solution=solution, contest=contest)
                    judge(solution)

                return redirect('contests:submission', contest.id, solution.id)
        else:
            form = None
        context = self.get_context_data(form=form, status=status)
        return render(request, self.template_name, context)


class SubmissionView(BaseContestView):
    tab = 'submit'
    template_name = 'contests/submission.html'

    def is_allowed(self, permissions):
        return permissions.submit

    def get(self, request, contest, solution_id):
        if not ContestSolution.objects.filter(contest=contest, solution_id=solution_id).exists():
            return redirect('contests:submit', contest.id)

        context = self.get_context_data(solution_id=solution_id)
        return render(request, self.template_name, context)


class MessagesView(BaseContestView):
    tab = 'messages'
    template_name = 'contests/messages.html'

    def is_allowed(self, permissions):
        return permissions.read_messages or permissions.manage_messages

    def _mark_as_read(self, qs):
        messages = list(qs)

        me = self.request.user
        if me.is_authenticated():
            read_message_ids = set(qs.filter(messageuser__user=me).values_list('pk', flat=True))
            unread_message_ids = set()

            print read_message_ids

            for message in messages:
                if message.pk not in read_message_ids:
                    unread_message_ids.add(message.pk)
                    message.is_unread = True

            # Yes, update database on HTTP GET request...
            if unread_message_ids:
                objs = [MessageUser(message_id=message_id, user=me) for message_id in unread_message_ids]
                try:
                    MessageUser.objects.bulk_create(objs)
                    pass
                except IntegrityError:
                    # unread counter is not critical for the competition
                    pass
        return messages

    def get(self, request, contest):
        qs = Message.objects.filter(message_type=Message.MESSAGE).order_by('-timestamp')
        if not self.permissions.manage_messages:
            qs = qs.filter(Q(recipient=request.user) | Q(recipient__isnull=True))

        messages = self._mark_as_read(qs)

        context = self.get_context_data(messages=messages)
        return render(request, self.template_name, context)


class QuestionsView(BaseContestView):
    tab = 'questions'
    template_name = 'contests/messages.html'

    def is_allowed(self, permissions):
        return permissions.read_messages or permissions.manage_messages

    def get(self, request, contest):
        messages = Message.objects.filter(message_type=Message.MESSAGE).order_by('-timestamp')
        if not self.permissions.manage_messages:
            messages = messages.filter(Q(recipient=request.user) | Q(recipient__isnull=True))

        context = self.get_context_data(messages=messages)
        return render(request, self.template_name, context)


class MessagesMixin(object):
    def to_message_list(self):
        return redirect('contests:messages', self.contest.id)


class NewMessageView(MessagesMixin, BaseContestView):
    tab = 'messages'
    template_name = 'contests/messages_form.html'

    def _make_form(self, data=None):
        recipient_id_choices = make_contestant_choices(self.contest, pgettext('to', 'all'))
        form = MessageForm(data=data, recipient_id_choices=recipient_id_choices)
        return form

    def is_allowed(self, permissions):
        return permissions.manage_messages

    def get(self, request, contest):
        form = self._make_form()
        context = self.get_context_data(form=form, new=True)
        return render(request, self.template_name, context)

    def post(self, request, contest):
        form = self._make_form(request.POST)
        if form.is_valid():
            message = form.save(commit=False)

            message.contest = contest
            message.recipient_id = form.cleaned_data['recipient_id']
            message.message_type = Message.MESSAGE
            message.timestamp = timezone.now()
            message.sender = request.user

            with transaction.atomic():
                message.save()
                MessageUser.objects.create(message=message, user=request.user)
            return self.to_message_list()

        context = self.get_context_data(form=form, new=True)
        return render(request, self.template_name, context)


class EditMessageView(MessagesMixin, BaseContestView):
    tab = 'messages'
    template_name = 'contests/messages_form.html'

    def is_allowed(self, permissions):
        return permissions.manage_messages

    def get(self, request, contest, message_id):
        message = Message.objects.filter(pk=message_id, contest=contest).first()
        if message is None:
            return self.to_message_list()

        form = MessageForm(instance=message)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, contest, message_id):
        message = Message.objects.filter(pk=message_id, contest=contest).first()
        if message is None:
            return self.to_message_list()

        form = MessageForm(request.POST, instance=message)
        if form.is_valid():
            form.save()
            return self.to_message_list()

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class DeleteMessageView(MessagesMixin, BaseContestView):
    tab = 'messages'
    template_name = 'contests/messages_delete.html'

    def is_allowed(self, permissions):
        return permissions.manage_messages

    def get(self, request, contest, message_id):
        message = Message.objects.filter(pk=message_id, contest=contest).first()
        if message is None:
            return self.to_message_list()

        context = self.get_context_data(message=message)
        return render(request, self.template_name, context)

    def post(self, request, contest, message_id):
        message = Message.objects.filter(pk=message_id, contest=contest).first()
        if message is None:
            return self.to_message_list()

        message.delete()
        return self.to_message_list()

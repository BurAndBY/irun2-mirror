from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.utils.translation import ugettext, pgettext
from django.views import generic

from api.queue import notify_enqueued
from common.constants import make_empty_select, EMPTY_SELECT
from common.networkutils import make_json_response
from common.pageutils import paginate
from problems.models import Problem
from problems.views import ProblemStatementMixin
from solutions.models import Solution
from solutions.utils import new_solution, judge
from storage.utils import serve_resource_metadata
from users.models import UserProfile

from .calcpermissions import calculate_contest_permissions
from .exporting import export_to_s4ris_json, export_to_ejudge_xml
from .forms import SolutionListUserForm, SolutionListProblemForm, ContestSolutionForm, MessageForm, AnswerForm, QuestionForm
from .forms import PrintoutForm, EditPrintoutForm
from .models import Contest, Membership, ContestSolution, Message, MessageUser, Printout, ContestUserRoom
from .services import make_contestant_choices, make_problem_choices, make_letter
from .services import ProblemResolver, ContestTiming
from .services import create_contest_service


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

        if self.permissions.answer_questions:
            qs = Message.objects.filter(contest=self.contest, message_type=Message.QUESTION, is_answered=False)
            context['unanswered_questions'] = qs.count()

        if self.permissions.ask_questions:
            qs = Message.objects.filter(contest=self.contest, message_type=Message.QUESTION, sender=me, messageuser__isnull=True)
            context['unread_answers'] = qs.count()

    def is_allowed(self, permissions):
        return False

    def dispatch(self, request, contest_id, *args, **kwargs):
        self.contest = get_object_or_404(Contest, pk=contest_id)
        self.service = create_contest_service(self.contest)
        self.timing = ContestTiming(self.contest)
        if request.user.is_authenticated():
            self.permissions = calculate_contest_permissions(self.contest, request.user, Membership.objects.filter(contest_id=contest_id, user=request.user))
        else:
            self.permissions = calculate_contest_permissions(self.contest, None, [])

        if not self.is_allowed(self.permissions):
            raise PermissionDenied()
        return super(BaseContestView, self).dispatch(request, self.contest, *args, **kwargs)


class ProblemResolverMixin(object):
    def get_context_data(self, **kwargs):
        context = super(ProblemResolverMixin, self).get_context_data(**kwargs)
        context['resolver'] = ProblemResolver(self.contest)
        return context


class GeneralView(BaseContestView):
    def is_allowed(self, permissions):
        return permissions.standings

    def get(self, request, contest):
        return redirect('contests:standings', contest.id)


AUTOREFRESH = 'autorefresh'


class StandingsView(BaseContestView):
    tab = 'standings'
    wide = False
    raw = False

    def get_template_name(self):
        if self.wide:
            return 'contests/standings_wide.html'
        if self.raw:
            return 'contests/standings_raw.html'

        return 'contests/standings.html'

    def is_allowed(self, permissions):
        return permissions.standings

    def get_context_data(self, **kwargs):
        context = super(StandingsView, self).get_context_data(**kwargs)
        context['no_standings_yet_message'] = self.service.get_no_standings_yet_message()
        return context

    def _parse_autorefresh(self, request):
        autorefresh = request.session.get(AUTOREFRESH, False)

        if AUTOREFRESH in request.GET:
            autorefresh_requested = (request.GET.get(AUTOREFRESH) == '1')
            if autorefresh != autorefresh_requested:
                request.session[AUTOREFRESH] = autorefresh_requested
                return autorefresh_requested

        return autorefresh

    def get(self, request, contest):
        autorefresh = self._parse_autorefresh(request)

        # privileged users may click on contestants to see their solutions
        user_url = reverse('contests:all_solutions', kwargs={'contest_id': contest.id}) if self.permissions.all_solutions else None
        my_id = request.user.id if request.user.is_authenticated() else None
        contest_results = None

        if self.service.are_standings_available(self.permissions, self.timing):
            # Do not show standings before the contest because they contain names of problems!
            frozen = (self.timing.is_freeze_applicable()) and (not self.permissions.always_unfrozen_standings)
            contest_results = self.service.make_contest_results(contest, frozen=frozen)

        context = self.get_context_data(results=contest_results, my_id=my_id, user_url=user_url, autorefresh=autorefresh)

        template_name = self.get_template_name()
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
        context['letter'] = ProblemResolver(contest).get_letter(problem.id)
        return render(request, self.template_name, context)


class AllSolutionsView(ProblemResolverMixin, BaseContestView):
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
        context['show_scores'] = not self.service.should_stop_on_fail()

        context = self.get_context_data(**context)
        return render(request, self.template_name, context)


class MySolutionsView(ProblemResolverMixin, BaseContestView):
    tab = 'my_solutions'
    template_name = 'contests/my_solutions.html'
    paginate_by = 25

    def is_allowed(self, permissions):
        return permissions.my_solutions

    def _make_problem_choices(self):
        if not self.permissions.problems_before and self.timing.get() == ContestTiming.BEFORE:
            return ((None, EMPTY_SELECT),)
        else:
            return make_problem_choices(self.contest)

    def get(self, request, contest):
        solutions = Solution.objects.all()\
            .filter(contestsolution__contest=contest, author=request.user)\
            .prefetch_related('compiler')\
            .select_related('source_code', 'best_judgement')\
            .order_by('-reception_time', 'id')

        problem_form = SolutionListProblemForm(data=request.GET, problem_choices=self._make_problem_choices())
        if problem_form.is_valid():
            solutions = solutions.filter(problem_id=problem_form.cleaned_data['problem'])

        context = paginate(request, solutions, self.paginate_by)

        context['problem_form'] = problem_form
        complete = self.service.should_show_my_solutions_completely(self.timing)
        context['complete'] = complete
        context['show_scores'] = complete and not self.service.should_stop_on_fail()

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

                    solution = new_solution(request, form, problem_id=form.cleaned_data['problem'], stop_on_fail=self.service.should_stop_on_fail())
                    ContestSolution.objects.create(solution=solution, contest=contest)
                    judge(solution)
                notify_enqueued()

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

'''
Messages
'''


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
                except IntegrityError:
                    pass  # unread counter is not critical for the competition
        return messages

    def get(self, request, contest):
        qs = contest.message_set.filter(message_type=Message.MESSAGE).order_by('-timestamp')
        if not self.permissions.manage_messages:
            qs = qs.filter(Q(recipient=request.user) | Q(recipient__isnull=True))

        messages = self._mark_as_read(qs)

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
        message = Message.objects.filter(pk=message_id, contest=contest, message_type=Message.MESSAGE).first()
        if message is None:
            return self.to_message_list()

        form = MessageForm(instance=message)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, contest, message_id):
        message = Message.objects.filter(pk=message_id, contest=contest, message_type=Message.MESSAGE).first()
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
        message = Message.objects.filter(pk=message_id, contest=contest, message_type=Message.MESSAGE).first()
        if message is None:
            return self.to_message_list()

        context = self.get_context_data(message=message)
        return render(request, self.template_name, context)

    def post(self, request, contest, message_id):
        message = Message.objects.filter(pk=message_id, contest=contest, message_type=Message.MESSAGE).first()
        if message is None:
            return self.to_message_list()

        message.delete()
        return self.to_message_list()

'''
Questions
'''


class AllQuestionsView(ProblemResolverMixin, BaseContestView):
    tab = 'all_questions'
    template_name = 'contests/all_questions.html'
    paginate_by = 7

    def is_allowed(self, permissions):
        return permissions.answer_questions

    def get(self, request, contest):
        qs = contest.message_set.filter(message_type=Message.QUESTION).order_by('-timestamp')
        context = paginate(request, qs, self.paginate_by)
        context = self.get_context_data(**context)
        return render(request, self.template_name, context)


class SingleQuestionMixin(object):
    def _load_question(self, message_id):
        question = self.contest.message_set.filter(pk=message_id, message_type=Message.QUESTION).first()
        return question


class AllQuestionsAnswersView(SingleQuestionMixin, ProblemResolverMixin, BaseContestView):
    tab = 'all_questions'
    template_name = 'contests/question_answers.html'

    def is_allowed(self, permissions):
        return permissions.answer_questions

    def _load_answers(self, question):
        answers = self.contest.message_set.filter(message_type=Message.ANSWER, parent=question).order_by('timestamp')
        return answers

    def get(self, request, contest, message_id):
        question = self._load_question(message_id)
        if question is None:
            return redirect('contests:all_questions', contest.id)

        answers = self._load_answers(question)
        form = AnswerForm(initial={'answers': len(answers)})

        context = self.get_context_data(question=question, answers=answers, form=form)
        return render(request, self.template_name, context)

    def post(self, request, contest, message_id):
        question = self._load_question(message_id)
        if question is None:
            return redirect('contests:all_questions', contest.id)

        already_answered = False
        answers = self._load_answers(question)
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer_count_old = form.cleaned_data['answers']
            answer_count_new = len(answers)
            if answer_count_old != answer_count_new:
                already_answered = True
                text = form.cleaned_data['text']
                form = AnswerForm(initial={'answers': answer_count_new, 'text': text})
            else:
                message = form.save(commit=False)

                message.contest = contest
                message.message_type = Message.ANSWER
                message.timestamp = timezone.now()
                message.sender = request.user
                message.parent = question

                with transaction.atomic():
                    message.save()
                    Message.objects.filter(pk=question.id).update(is_answered=True)
                    MessageUser.objects.filter(message=question).delete()

                return redirect('contests:all_questions', contest.id)

        context = self.get_context_data(question=question, answers=answers, form=form, already_answered=already_answered)
        return render(request, self.template_name, context)


class AllQuestionsDeleteView(SingleQuestionMixin, ProblemResolverMixin, BaseContestView):
    tab = 'all_questions'
    template_name = 'contests/all_questions_delete.html'

    def is_allowed(self, permissions):
        return permissions.answer_questions

    def get(self, request, contest, message_id):
        question = self._load_question(message_id)
        if question is None:
            return redirect('contests:all_questions', contest.id)
        context = self.get_context_data(question=question)
        return render(request, self.template_name, context)

    def post(self, request, contest, message_id):
        question = self._load_question(message_id)
        if question is None:
            return redirect('contests:all_questions', contest.id)
        question.delete()
        return redirect('contests:all_questions', contest.id)


class MyQuestionsView(ProblemResolverMixin, BaseContestView):
    tab = 'my_questions'
    template_name = 'contests/my_questions.html'
    paginate_by = 7

    def is_allowed(self, permissions):
        return permissions.ask_questions

    def get(self, request, contest):
        qs = contest.message_set.filter(message_type=Message.QUESTION, sender=request.user).order_by('-timestamp')
        questions = list(qs)

        me = self.request.user
        if me.is_authenticated():
            read_message_ids = set(qs.filter(messageuser__user=me).values_list('pk', flat=True))
            for question in questions:
                if question.pk not in read_message_ids:
                    question.is_unread = True

        context = self.get_context_data(questions=questions)
        return render(request, self.template_name, context)


class MyQuestionsNewView(ProblemResolverMixin, BaseContestView):
    tab = 'my_questions'
    template_name = 'contests/my_questions_form.html'
    paginate_by = 7

    def is_allowed(self, permissions):
        return permissions.ask_questions

    def _make_form(self, data=None):
        general_question = make_empty_select(ugettext('General question'))
        if not self.permissions.problems_before and self.timing.get() == ContestTiming.BEFORE:
            # do not show problem names before the contest
            problem_id_choices = ((None, general_question),)
        else:
            problem_id_choices = make_problem_choices(self.contest, general_question)

        form = QuestionForm(data=data, problem_id_choices=problem_id_choices)
        return form

    def get(self, request, contest):
        form = self._make_form()
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, contest):
        form = self._make_form(request.POST)
        if form.is_valid():
            message = form.save(commit=False)

            message.contest = contest
            message.problem_id = form.cleaned_data['problem_id']
            message.message_type = Message.QUESTION
            message.timestamp = timezone.now()
            message.sender = request.user

            with transaction.atomic():
                message.save()
                MessageUser.objects.create(message=message, user=request.user)

            messages.add_message(self.request, messages.INFO, ugettext('The question has been successfully submitted.'))
            return redirect('contests:my_questions', contest.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class MyQuestionsAnswersView(ProblemResolverMixin, BaseContestView):
    tab = 'my_questions'
    template_name = 'contests/question_answers.html'

    def is_allowed(self, permissions):
        return permissions.ask_questions

    def _load_answers(self, question):
        answers = self.contest.message_set.\
            filter(message_type=Message.ANSWER, parent=question).\
            order_by('timestamp')
        return answers

    def _mark_as_read(self, question):
        kwargs = {'message': question, 'user': self.request.user}
        if not MessageUser.objects.filter(**kwargs).exists():
            try:
                MessageUser.objects.create(**kwargs)
            except IntegrityError:
                pass  # unread counter is not critical for the competition

    def get(self, request, contest, message_id):
        question = self.contest.message_set.filter(pk=message_id, sender=request.user, message_type=Message.QUESTION).first()
        if question is None:
            return redirect('contests:my_questions', contest.id)

        answers = self._load_answers(question)
        self._mark_as_read(question)
        context = self.get_context_data(question=question, answers=answers)
        return render(request, self.template_name, context)

'''
Compilers
'''


class CompilersView(BaseContestView):
    tab = 'compilers'
    template_name = 'contests/compilers.html'

    def is_allowed(self, permissions):
        return permissions.compilers

    def get(self, request, contest):
        compilers = contest.compilers.select_related('compilerdetails').order_by('description')
        context = self.get_context_data(compilers=compilers)
        return render(request, self.template_name, context)


'''
Export
'''


class ExportView(BaseContestView):
    tab = 'export'
    template_name = 'contests/export.html'

    def is_allowed(self, permissions):
        return permissions.export

    def get(self, request, contest):
        context = self.get_context_data()
        return render(request, self.template_name, context)


class S4RiSExportView(ExportView):
    def get(self, request, contest):
        results = self.service.make_contest_results(contest, frozen=False)
        json = export_to_s4ris_json(contest, results)
        return make_json_response(json)


class EjudgeExportView(ExportView):
    def get(self, request, contest):
        results = self.service.make_contest_results(contest, frozen=False)
        xml = export_to_ejudge_xml(contest, results)
        return HttpResponse(xml, content_type='application/xml; charset=utf-8')


'''
Printing
'''


class PrintingView(BaseContestView):
    tab = 'printing'
    template_name = 'contests/printing.html'
    paginate_by = 25

    def is_allowed(self, permissions):
        return permissions.printing

    def get(self, request, contest):

        qs = Printout.objects.filter(contest=contest).order_by('-timestamp')

        context = paginate(request, qs, self.paginate_by)
        context['enable_links'] = self.permissions.manage_printing
        context['show_author'] = self.permissions.manage_printing
        context = self.get_context_data(**context)

        return render(request, self.template_name, context)


class NewPrintoutView(BaseContestView):
    tab = 'printing'
    template_name = 'contests/printout_new.html'

    def is_allowed(self, permissions):
        return permissions.printing

    def _make_form(self, data=None):
        room = None
        cur = ContestUserRoom.objects.filter(contest=self.contest, user=self.request.user).first()
        if cur is not None:
            room = cur.room

        form = PrintoutForm(data=data, rooms=self.contest.rooms, initial={'room': room})
        return form

    def _get_status(self):
        if self.permissions.manage_printing:
            return True
        return (self.timing.get() == ContestTiming.IN_PROGRESS)

    def get(self, request, contest):
        enabled = self._get_status()
        form = self._make_form() if enabled else None
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, contest):
        enabled = self._get_status()
        if enabled:
            form = self._make_form(request.POST)
            if form.is_valid():
                printout = form.save(commit=False)
                printout.contest = contest
                printout.user = request.user
                printout.timestamp = timezone.now()
                with transaction.atomic():
                    printout.save()
                    # remember used room to select it again later
                    ContestUserRoom.objects.update_or_create(contest=contest, user=request.user, defaults={'room': printout.room})
                messages.add_message(self.request, messages.INFO, ugettext('Your printout has been successfully added to printing queue.'))
                return redirect('contests:printing', contest.id)
        else:
            form = None
        context = self.get_context_data(form=form, enable_links=True)
        return render(request, self.template_name, context)


class ShowPrintoutView(BaseContestView):
    tab = 'printing'
    template_name = 'contests/printout_show.html'

    def is_allowed(self, permissions):
        return permissions.manage_printing

    def get(self, request, contest, printout_id):
        printout = get_object_or_404(Printout, pk=printout_id, contest=contest)
        context = self.get_context_data(printout=printout)
        return render(request, self.template_name, context)


class EditPrintoutView(BaseContestView):
    tab = 'printing'
    template_name = 'contests/printout_edit.html'

    def is_allowed(self, permissions):
        return permissions.manage_printing

    def get(self, request, contest, printout_id):
        printout = get_object_or_404(Printout, pk=printout_id, contest=contest)
        form = EditPrintoutForm(instance=printout)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, contest, printout_id):
        printout = get_object_or_404(Printout, pk=printout_id, contest=contest)
        form = EditPrintoutForm(request.POST, instance=printout)
        if form.is_valid():
            form.save()
            return redirect('contests:printing', contest.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

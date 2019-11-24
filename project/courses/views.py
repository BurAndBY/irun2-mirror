# -*- coding: utf-8 -*-

import calendar
import json
from collections import namedtuple

from django.contrib import auth
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.decorators import method_decorator
from django.views import generic
from django.http import HttpResponse, JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from cauth.mixins import StaffMemberRequiredMixin
from common.cast import str_to_uint
from common.constants import make_empty_select
from common.pageutils import paginate
from common.outcome import Outcome
from common.statutils import build_proglangbars
from problems.models import (
    Problem,
    ProblemFolder,
    ProblemRelatedFile,
)
from problems.views import ProblemStatementMixin
from proglangs.utils import get_ace_mode
from solutions.filters import apply_state_filter
from solutions.forms import AllSolutionsFilterForm
from solutions.models import Solution
from solutions.utils import (
    judge,
    new_solution,
)
from storage.utils import serve_resource_metadata

from courses.forms import (
    ActivityRecordFakeForm,
    SolutionForm,
    SolutionListProblemForm,
    SolutionListUserForm,
)
from courses.forms import (
    MailMessageForm,
    MailResolvedForm,
    MailThreadForm,
)
from courses.models import (
    Activity,
    ActivityRecord,
    Assignment,
    Course,
    CourseSolution,
    CourseStatus,
    Criterion,
    MailMessage,
    Membership,
    Topic,
    TopicCommonProblem,
)
from courses.services import (
    UserCache,
    make_problem_choices,
    make_student_choices,
    make_allusers_choices,
    make_course_results,
    make_course_single_result,
)
from courses.services import (
    get_assigned_problem_set,
    get_simple_assignments,
    get_attempt_quota,
    get_attempt_message,
)
from courses.calcpermissions import calculate_course_permissions
from courses.messaging import (
    list_mail_threads,
    get_unread_thread_count,
    is_unread,
    update_last_viewed_timestamp,
    post_message,
)

EditorialFile = namedtuple('EditorialFile', 'filename description')


class BaseCourseView(generic.View):
    tab = None
    subtab = None

    def __init__(self, *args, **kwargs):
        super(BaseCourseView, self).__init__(*args, **kwargs)
        self._user_cache = None

    def get_context_data(self, **kwargs):
        context = {
            'course': self.course,
            'course_is_archived': self.course.status == CourseStatus.ARCHIVED,
            'permissions': self.permissions,
            'active_tab': self.tab,
            'active_subtab': self.subtab,
            'unread': get_unread_thread_count(self.course, self.request.user, self.permissions)
        }
        context.update(kwargs)
        return context

    def is_allowed(self, permissions):
        return False

    def get_user_cache(self):
        if self._user_cache is not None:
            return self._user_cache
        self._user_cache = UserCache(self.course)
        return self._user_cache

    @method_decorator(auth.decorators.login_required)
    def dispatch(self, request, course_id, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=course_id)
        self.permissions = calculate_course_permissions(
            self.course, request.user, Membership.objects.filter(course_id=course_id, user=request.user)
        )

        if not self.is_allowed(self.permissions):
            raise PermissionDenied()
        return super(BaseCourseView, self).dispatch(request, self.course, *args, **kwargs)


class UserCacheMixinMixin(object):
    def get_context_data(self, **kwargs):
        context = super(UserCacheMixinMixin, self).get_context_data(**kwargs)
        context['user_cache'] = self.get_user_cache()
        return context


class CourseInfoView(BaseCourseView):
    tab = 'info'
    template_name = 'courses/info.html'

    def is_allowed(self, permissions):
        return permissions.info

    def _make(self, solutions):
        return [
            (calendar.timegm(reception_time.timetuple()) * 1000, i + 1)
            for i, reception_time in enumerate(solutions.values_list('reception_time', flat=True))
        ]

    def get(self, request, course):
        student_user_ids = Membership.objects.filter(course=course, role=Membership.STUDENT).values_list('user_id', flat=True)

        user_cache = self.get_user_cache()
        student_user_ids = [user.id for user in user_cache.list_students()]

        solutions = Solution.objects.all()\
            .filter(coursesolution__course=course)\
            .filter(author_id__in=student_user_ids)\
            .order_by('reception_time')

        accepted_solutions = solutions.filter(best_judgement__outcome=Outcome.ACCEPTED)

        all_solution_data = self._make(solutions)
        accepted_solution_data = self._make(accepted_solutions)

        if accepted_solution_data and all_solution_data:
            if accepted_solution_data[-1][0] != all_solution_data[-1][0]:
                accepted_solution_data.append((all_solution_data[-1][0], accepted_solution_data[-1][1]))

        show_activity_plot = (len(all_solution_data) > 0)

        latest_accepted_solutions = accepted_solutions.order_by('-reception_time')[:7]

        language_bars = build_proglangbars(solutions)

        return render(request, self.template_name, self.get_context_data(
            show_activity_plot=show_activity_plot,
            all_solution_json=json.dumps(all_solution_data),
            accepted_solution_json=json.dumps(accepted_solution_data),
            user_cache=user_cache,
            latest_accepted_solutions=latest_accepted_solutions,
            language_bars=language_bars,
        ))


class CourseSheetView(UserCacheMixinMixin, BaseCourseView):
    tab = 'sheet'
    template_name = 'courses/sheet.html'

    def is_allowed(self, permissions):
        return permissions.sheet

    def get(self, request, course):
        data = make_course_results(course)
        context = self.get_context_data(data=data)
        return render(request, self.template_name, context)


class CourseSheetEditView(UserCacheMixinMixin, BaseCourseView):
    tab = 'sheet'
    template_name = 'courses/sheet.html'

    def is_allowed(self, permissions):
        return permissions.sheet_edit

    def get(self, request, course):
        data = make_course_results(course)
        context = self.get_context_data(data=data, edit_mode=True, choices=ActivityRecord.CHOICES)
        return render(request, self.template_name, context)


class CourseSheetEditApiView(BaseCourseView):
    def is_allowed(self, permissions):
        return permissions.sheet_edit

    def post(self, request, course, membership_id, activity_id):
        if not Membership.objects.filter(pk=membership_id, course=course).exists():
            raise Http404('no such membership in the course')

        if not Activity.objects.filter(pk=activity_id, course=course).exists():
            raise Http404('no such activity in the course')

        form = ActivityRecordFakeForm(request.POST)
        if form.is_valid():
            to_update = {}
            for k, v in form.cleaned_data.items():
                if v is not None:
                    to_update[k] = v

            if len(to_update) > 0:
                ActivityRecord.objects.update_or_create(defaults=to_update, membership_id=membership_id, activity_id=activity_id)

            return HttpResponse('OK')

        return HttpResponse('Error', status=400)

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CourseSheetEditApiView, self).dispatch(*args, **kwargs)


class CourseSubmitView(BaseCourseView):
    tab = 'submit'
    template_name = 'courses/submit.html'

    def is_allowed(self, permissions):
        return permissions.submit

    def _make_choices(self):
        return make_problem_choices(self.course, full=self.permissions.submit_all_problems, user_id=self.request.user.id)

    def _make_initial(self):
        initial = {}

        problem_id = self.request.GET.get('problem')
        if problem_id is not None:
            try:
                problem_id = int(problem_id)
            except (TypeError,):
                problem_id = None

        if problem_id:
            initial['problem'] = problem_id

        last_used_compiler = self.request.user.userprofile.last_used_compiler
        if last_used_compiler is not None:
            initial['compiler'] = last_used_compiler

        return initial

    def _make_form(self, data=None, files=None):
        def check_limit(problem_id):
            quota, _ = get_attempt_quota(self.course, self.request.user, problem_id)
            return quota == 0

        form = SolutionForm(
            data=data,
            files=files,
            problem_choices=self._make_choices(),
            compiler_queryset=self.course.compilers,
            attempt_limit_checker=check_limit,
            initial=self._make_initial(),
        )
        return form

    def _post_valid_form(self, request, course, form):
        with transaction.atomic():
            # remember used compiler to select it again later
            userprofile = request.user.userprofile
            userprofile.last_used_compiler = form.cleaned_data['compiler']
            userprofile.save()

            solution = new_solution(request, form, problem_id=form.cleaned_data['problem'])
            CourseSolution.objects.create(solution=solution, course=course)
            notifier = judge(solution)
        notifier.notify()
        return solution

    def get(self, request, course):
        form = self._make_form()
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course):
        form = self._make_form(request.POST, request.FILES)
        if form.is_valid():
            solution = self._post_valid_form(request, course, form)
            return redirect('courses:course_submission', course.id, solution.id)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class CourseSubmit2View(CourseSubmitView):
    template_name = 'courses/submit2.html'

    def get_context_data(self, **kwargs):
        context = super(CourseSubmit2View, self).get_context_data(**kwargs)
        context['ace_modes'] = [(compiler.id, get_ace_mode(compiler.language)) for compiler in self.course.compilers.all()]
        return context

    def post(self, request, course):
        form = self._make_form(request.POST, request.FILES)
        if form.is_valid():
            solution = self._post_valid_form(request, course, form)
            response = {
                'submitted': True,
                'solutionId': solution.id,
                'attempts': get_attempt_message(course, request.user, solution.problem_id)
            }
        else:
            response = {
                'submitted': False,
                'errors': [smart_text(e) for errors in form.errors.values() for e in errors]
            }
        return JsonResponse(response, json_dumps_params={'ensure_ascii': False})


class CourseSubmissionView(BaseCourseView):
    tab = 'submit'
    template_name = 'courses/submission.html'

    def is_allowed(self, permissions):
        return permissions.submit

    def get(self, request, course, solution_id):
        if not CourseSolution.objects.filter(course=course, solution_id=solution_id).exists():
            raise Http404('solution does not exist in the course')

        context = self.get_context_data(solution_id=solution_id)
        return render(request, self.template_name, context)


'''
Problems
'''


class CourseProblemsView(BaseCourseView):
    tab = 'problems'
    template_name = 'courses/problems_base.html'

    def is_allowed(self, permissions):
        return permissions.problems

    def get(self, request, course):
        topics = course.topic_set.all()

        context = self.get_context_data(topics=topics, navigate_topics=True)
        return render(request, self.template_name, context)


class CourseProblemsTopicView(BaseCourseView):
    tab = 'problems'
    template_name = 'courses/problems_list.html'

    def is_allowed(self, permissions):
        return permissions.problems

    def get(self, request, course, topic_id):
        topic = course.topic_set.filter(id=topic_id).first()
        if topic is None:
            return redirect('courses:course_problems', course_id=course.id)

        assigned_problems = get_assigned_problem_set(course)

        problems_with_assign_flag = []
        for problem in topic.list_problems():
            assigned = (problem.id in assigned_problems)
            problems_with_assign_flag.append((problem, assigned))

        context = self.get_context_data()
        topics = course.topic_set.all()
        context['navigate_topics'] = True
        context['topics'] = topics
        context['active_topic'] = topic
        context['problems'] = problems_with_assign_flag
        return render(request, self.template_name, context)


def _locate_in_list(lst, x):
    try:
        pos = lst.index(x)
    except ValueError:
        return None
    length = len(lst)
    return ((pos + length - 1) % length, pos, (pos + 1) % length)


class CourseStatementMixin(object):
    def get_context_data(self, **kwargs):
        context = super(CourseStatementMixin, self).get_context_data(**kwargs)
        can_submit = False

        simple_assignments = get_simple_assignments(self.course, self.problem)

        if self.permissions.submit_all_problems:
            can_submit = True
        else:
            me = self.request.user.id
            can_submit = any((x.user_id == me) for x in simple_assignments)
            if not can_submit:
                can_submit |= self.course.common_problems.filter(pk=self.problem.id).exists()
            if not can_submit:
                can_submit |= TopicCommonProblem.objects.filter(topic__course=self.course, problem=self.problem).exists()

        if self.permissions.editorials:
            context['editorial_files'] = [
                EditorialFile(prf.filename, prf.description)
                for prf in self.problem.problemrelatedfile_set.filter(file_type=ProblemRelatedFile.SOLUTION_DESCRIPTION)
            ]

        if simple_assignments:
            context['simple_assignments'] = simple_assignments
            context['user_cache'] = self.get_user_cache()
        context['can_submit'] = can_submit
        return context


class CourseProblemsTopicProblemView(ProblemStatementMixin, CourseStatementMixin, BaseCourseView):
    tab = 'problems'
    template_name = 'courses/problems_statement.html'

    def is_allowed(self, permissions):
        return permissions.problems

    def get(self, request, course, topic_id, problem_id, filename):
        topic = get_object_or_404(Topic, pk=topic_id, course_id=course.id)
        if topic.problem_folder is None:
            return redirect('courses:course_problems', course_id=course.id)

        problem = topic.problem_folder.problem_set.filter(pk=problem_id).first()
        if problem is None:
            return redirect('courses:course_problems_topic', course_id=course.id, topic_id=topic.id)
        self.problem = problem

        if self.is_aux_file(filename):
            return self.serve_aux_file(request, problem.id, filename)

        problem_ids = topic.problem_folder.problem_set.order_by('number', 'subnumber').values_list('id', flat=True)
        problem_ids = list(problem_ids)  # evaluate the queryset
        problem_id = int(problem_id)  # safe because of regexp in urls.py

        positions = _locate_in_list(problem_ids, problem_id)
        if positions is not None:
            context = self.get_context_data()
            prev, cur, next = positions

            context['navigate_topics'] = True
            context['prev_next'] = True
            context['prev_problem_id'] = problem_ids[prev]
            context['cur_position'] = cur + 1  # 1-based
            context['total_positions'] = len(problem_ids)
            context['next_problem_id'] = problem_ids[next]
            context['problem'] = problem
            context['statement'] = self.make_statement(problem)

            context['topics'] = course.topic_set.all()
            context['active_topic'] = topic
            return render(request, self.template_name, context)

        # fallback
        return redirect('courses:course_problems', course_id=course.id)


class CourseProblemsProblemView(ProblemStatementMixin, CourseStatementMixin, BaseCourseView):
    tab = 'problems'
    template_name = 'courses/problems_statement.html'

    def is_allowed(self, permissions):
        if not permissions.problems:
            return False

        # We show the statement if the problem belongs to the set of problems that can be assigned now
        course_id = self.kwargs['course_id']
        problem_id = self.kwargs['problem_id']

        course_folders = ProblemFolder.objects.filter(topic__course_id=course_id)
        problem_folders = ProblemFolder.objects.filter(problem__id=problem_id)

        if (course_folders & problem_folders).exists():
            return True

        # We show the problem if it has already been assigned
        if Assignment.objects.filter(membership__course_id=course_id, problem_id=problem_id).exists():
            return True

        # We show the problem if it has already been submitted in the course
        if CourseSolution.objects.filter(course_id=course_id, solution__problem_id=problem_id).exists():
            return True

        # We show the problem if it is present in the list of common problems for course.
        if self.course.common_problems.filter(pk=problem_id).exists():
            return True

        if TopicCommonProblem.objects.filter(topic__course_id=course_id, problem_id=problem_id).exists():
            return True

        return False

    def get(self, request, course, problem_id, filename):
        problem = get_object_or_404(Problem, pk=problem_id)
        self.problem = problem

        if self.is_aux_file(filename):
            return self.serve_aux_file(request, problem.id, filename)

        context = self.get_context_data()
        context['navigate_topics'] = False
        context['problem'] = problem
        context['statement'] = self.make_statement(problem)
        return render(request, self.template_name, context)


class CourseStandingsView(UserCacheMixinMixin, BaseCourseView):
    tab = 'standings'
    template_name = 'courses/standings.html'

    def is_allowed(self, permissions):
        return permissions.standings

    def get(self, request, course):
        context = self.get_context_data()
        res = make_course_results(course)
        context['course_descr'] = res.course_descr
        context['results'] = res.user_results
        return render(request, self.template_name, context)


class CourseStandingsWideView(CourseStandingsView):
    template_name = 'courses/standings_wide.html'


'''
Criterion
'''


class CriterionListView(StaffMemberRequiredMixin, generic.ListView):
    model = Criterion


class CriterionCreateView(StaffMemberRequiredMixin, generic.CreateView):
    model = Criterion
    fields = ['label', 'name']

    def get_context_data(self, **kwargs):
        context = super(CriterionCreateView, self).get_context_data(**kwargs)
        context['page_title'] = _('New criterion')
        return context

    def get_success_url(self):
        return reverse('courses:criterion_index')


class CriterionUpdateView(StaffMemberRequiredMixin, generic.UpdateView):
    model = Criterion
    fields = ['label', 'name']

    def get_context_data(self, **kwargs):
        context = super(CriterionUpdateView, self).get_context_data(**kwargs)
        context['page_title'] = _('Edit criterion')
        return context

    def get_success_url(self):
        return reverse('courses:criterion_index')


class CriterionDeleteView(StaffMemberRequiredMixin, generic.View):
    template_name = 'courses/criterion_confirm_delete.html'

    def list_courses(self, criterion_id):
        return list(Course.objects.filter(topic__criteria__id=criterion_id).distinct())

    def get(self, request, pk):
        criterion = get_object_or_404(Criterion, pk=pk)
        course_list = self.list_courses(criterion.id)
        context = {'course_list': course_list}
        return render(request, self.template_name, context)

    def post(self, request, pk):
        criterion = get_object_or_404(Criterion, pk=pk)
        course_list = self.list_courses(criterion.id)
        if not course_list:
            criterion.delete()
        return redirect('courses:criterion_index')


'''
Solutions list
'''


class CourseAllSolutionsView(BaseCourseView):
    tab = 'all_solutions'
    template_name = 'courses/solutions.html'
    paginate_by = 25

    def is_allowed(self, permissions):
        return permissions.all_solutions

    def get(self, request, course):
        # filters
        user_id = None
        problem_id = None
        state = None

        # User filter

        user_cache = self.get_user_cache()
        empty_select = make_empty_select(_('Student'))
        user_form = SolutionListUserForm(data=request.GET, user_choices=make_student_choices(user_cache, empty_select=empty_select))

        if user_form.is_valid():
            user_id = user_form.cleaned_data['user']

        # Problem filter

        empty_select = make_empty_select(_('Problem'))
        if user_id is not None:
            problem_choices = make_problem_choices(course, user_id=user_id, empty_select=empty_select)
        else:
            problem_choices = make_problem_choices(course, full=True, empty_select=empty_select)

        problem_form = SolutionListProblemForm(data=request.GET, problem_choices=problem_choices)
        if problem_form.is_valid():
            problem_id = problem_form.cleaned_data['problem']

        # State filter

        filter_form = AllSolutionsFilterForm(request.GET)
        if filter_form.is_valid():
            state = filter_form.cleaned_data['state']

        # Apply filters

        solutions = Solution.objects.all()\
            .filter(coursesolution__course=course)\
            .prefetch_related('compiler')\
            .select_related('problem', 'source_code', 'best_judgement', 'aggregatedresult')\
            .order_by('-reception_time', 'id')

        if user_id is not None:
            solutions = solutions.filter(author_id=user_id)

        if problem_id is not None:
            solutions = solutions.filter(problem_id=problem_id)

        if state is not None:
            solutions = apply_state_filter(solutions, state)

        context = paginate(request, solutions, self.paginate_by)

        context['user_form'] = user_form
        context['problem_form'] = problem_form
        context['filter_form'] = filter_form
        context['user_cache'] = user_cache
        context['page_title'] = _('All solutions')

        # tune visual representation for better fitting screen width
        context['show_author'] = True
        context['show_compilerbox'] = True
        context['show_filename'] = False
        context['show_verbose_outcome'] = False
        context['show_outcome_tooltip'] = True

        context = self.get_context_data(**context)
        return render(request, self.template_name, context)


class CourseMySolutionsView(BaseCourseView):
    tab = 'my_solutions'
    template_name = 'courses/solutions.html'
    paginate_by = 25

    def is_allowed(self, permissions):
        return permissions.my_solutions

    def get(self, request, course):
        empty_select = make_empty_select(_('Problem'))
        problem_choices = make_problem_choices(course, user_id=request.user.id, empty_select=empty_select)
        problem_form = SolutionListProblemForm(data=request.GET, problem_choices=problem_choices)
        if problem_form.is_valid():
            problem_id = problem_form.cleaned_data['problem']
        else:
            problem_id = None

        solutions = Solution.objects.all()\
            .filter(coursesolution__course=course, author=request.user)\
            .prefetch_related('compiler')\
            .select_related('problem', 'source_code', 'best_judgement')\
            .order_by('-reception_time', 'id')

        if problem_id is not None:
            solutions = solutions.filter(problem_id=problem_id)

        context = paginate(request, solutions, self.paginate_by)
        context['problem_form'] = problem_form
        context['page_title'] = _('My solutions')

        # tune visual representation for better fitting screen width
        context['show_author'] = False  # all solutions belong to the same author
        context['show_compilerbox'] = True
        context['show_filename'] = True
        context['show_verbose_outcome'] = True
        context['show_outcome_tooltip'] = False

        context = self.get_context_data(**context)
        return render(request, self.template_name, context)


'''
My problems
'''


class CourseMyProblemsView(BaseCourseView):
    tab = 'my_problems'
    template_name = 'courses/my_problems.html'

    def is_allowed(self, permissions):
        return permissions.messages

    def get(self, request, course):
        membership = get_object_or_404(Membership, course=course, user=request.user, role=Membership.STUDENT)
        user_result = make_course_single_result(course, membership, request.user)
        context = self.get_context_data(user_result=user_result)
        return render(request, self.template_name, context)


'''
My attempts
'''


class CourseMyAttemptsView(BaseCourseView):
    def is_allowed(self, permissions):
        return permissions.submit

    def get(self, request, course):
        problem_id = str_to_uint(request.GET.get('problem'))
        message = get_attempt_message(course, request.user, problem_id)
        return JsonResponse({'message': message})


'''
Messages
'''


class CourseMessagesEmptyView(BaseCourseView):
    tab = 'messages'
    template_name = 'courses/messages.html'

    def is_allowed(self, permissions):
        return permissions.messages

    def get(self, request, course):
        threads = list_mail_threads(course, request.user, self.permissions)
        context = self.get_context_data(threads=threads, thread_id=None, user_cache=self.get_user_cache())
        return render(request, self.template_name, context)


class CourseMessagesSingleThreadView(BaseCourseView):
    tab = 'messages'
    template_name = 'courses/messages.html'

    def is_allowed(self, permissions):
        return permissions.messages

    def _load_thread(self, thread_id):
        self.threads = list_mail_threads(self.course, self.request.user, self.permissions)
        self.thread_id = str_to_uint(thread_id)

        thread = None
        for cur_thread in self.threads:
            if cur_thread.id == self.thread_id:
                thread = cur_thread
                break
        if thread is None:
            raise Http404('Thread not found')

        self.thread = thread
        return thread

    def get_context_data(self, **kwargs):
        context = super(CourseMessagesSingleThreadView, self).get_context_data(**kwargs)
        context['threads'] = self.threads
        context['thread'] = self.thread
        context['user_cache'] = self.get_user_cache()
        context['can_delete'] = self.permissions.messages_delete_thread
        return context


class CourseMessagesView(CourseMessagesSingleThreadView):
    def _load_messages(self, thread):
        messages = []
        for message in MailMessage.objects.filter(thread=thread).\
                select_related('attachment').\
                order_by('timestamp'):
            message.unread = is_unread(self.thread.last_viewed_timestamp, message.timestamp)
            messages.append(message)
        return messages

    def get(self, request, course, thread_id):
        thread = self._load_thread(thread_id)
        messages = self._load_messages(thread)
        message_form = MailMessageForm()

        # must be run before get_context_data to get unread counter in the sidebar decreased
        if thread.unread:
            update_last_viewed_timestamp(request.user, thread, timezone.now())

        context = self.get_context_data(messages=messages, message_form=message_form)
        return render(request, self.template_name, context)

    def post(self, request, course, thread_id):
        thread = self._load_thread(thread_id)
        messages = self._load_messages(thread)

        message_form = MailMessageForm(request.POST, request.FILES)
        if message_form.is_valid():
            post_message(request.user, thread, message_form, self.permissions.messages_all)
            return redirect('courses:messages', course.id, thread_id)

        context = self.get_context_data(messages=messages, message_form=message_form)
        return render(request, self.template_name, context)


class CourseMessagesDownloadView(CourseMessagesSingleThreadView):
    def get(self, request, course, thread_id, message_id, filename):
        thread = self._load_thread(thread_id)
        message = get_object_or_404(
            MailMessage.objects.select_related('attachment'),
            pk=message_id, thread=thread, attachment__filename=filename)
        return serve_resource_metadata(request, message.attachment)


class CourseMessagesThreadDeleteView(CourseMessagesSingleThreadView):
    def post(self, request, course, thread_id):
        thread = self._load_thread(thread_id)
        if self.permissions.messages_delete_thread:
            thread.delete()
        return redirect('courses:messages_empty', course.id)


class CourseMessagesThreadResolveView(CourseMessagesSingleThreadView):
    def post(self, request, course, thread_id):
        thread = self._load_thread(thread_id)
        if self.permissions.messages_resolve:
            form = MailResolvedForm(request.POST)
            if form.is_valid():
                thread.resolved = form.cleaned_data['resolved']
                thread.save()
        return JsonResponse({})


class CourseMessagesNewView(BaseCourseView):
    tab = 'messages'
    template_name = 'courses/messages_new.html'

    general_question = make_empty_select(_('General question'))
    all_users = make_empty_select(_('All'))

    def is_allowed(self, permissions):
        return permissions.messages_send_any or permissions.messages_send_own

    def _make_forms(self, data=None, files=None):
        if self.permissions.messages_send_any:
            problem_choices = make_problem_choices(self.course, full=True, empty_select=self.general_question)
            person_choices = make_allusers_choices(self.get_user_cache(), empty_select=self.all_users)
        else:
            problem_choices = make_problem_choices(self.course, user_id=self.request.user.id, empty_select=self.general_question)
            person_choices = None

        thread_form = MailThreadForm(data=data, files=files, problem_choices=problem_choices, person_choices=person_choices)

        message_form = MailMessageForm(data=data, files=files)
        return (thread_form, message_form)

    def get(self, request, course):
        thread_form, message_form = self._make_forms()
        context = self.get_context_data(thread_form=thread_form, message_form=message_form)
        return render(request, self.template_name, context)

    def post(self, request, course):
        thread_form, message_form = self._make_forms(data=request.POST, files=request.FILES)
        if thread_form.is_valid() and message_form.is_valid():
            with transaction.atomic():
                thread = thread_form.save(commit=False)
                thread.course = course
                thread.problem_id = thread_form.cleaned_data['problem']
                if 'person' in thread_form.cleaned_data:
                    thread.person_id = thread_form.cleaned_data['person']
                else:
                    thread.person_id = request.user.id

                post_message(request.user, thread, message_form, self.permissions.messages_all)
                return redirect('courses:messages', course.id, thread.id)

        context = self.get_context_data(thread_form=thread_form, message_form=message_form)
        return render(request, self.template_name, context)


class CourseCompilersView(BaseCourseView):
    tab = 'compilers'
    template_name = 'courses/compilers.html'

    def is_allowed(self, permissions):
        return permissions.info

    def get(self, request, course):
        compilers = course.compilers.select_related('compilerdetails').order_by('description')
        context = self.get_context_data(compilers=compilers)
        return render(request, self.template_name, context)

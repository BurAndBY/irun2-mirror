# -*- coding: utf-8 -*-

import calendar
import json
from collections import namedtuple

from django.contrib import auth
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.decorators import method_decorator
from django.views import generic
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from forms import SolutionForm, ProblemAssignmentForm, AddExtraProblemSlotForm, SolutionListMemberForm, SolutionListProblemForm, ActivityRecordFakeForm
from models import Course, Topic, Membership, Assignment, Criterion, CourseSolution, Activity, ActivityRecord
from services import make_problem_choices, make_course_results, make_course_single_result
from permissions import CoursePermissions

from common.pageutils import paginate
from common.cacheutils import AllObjectsCache
from common.views import StaffMemberRequiredMixin
from problems.models import Problem, ProblemFolder
from problems.views import ProblemStatementMixin
from proglangs.models import Compiler
from solutions.models import Solution
from solutions.utils import new_solution, judge


class BaseCourseView(generic.View):
    tab = None
    subtab = None

    def get_context_data(self, **kwargs):
        context = {
            'course': self.course,
            'permissions': self.permissions,
            'active_tab': self.tab,
            'active_subtab': self.subtab,
        }
        context.update(kwargs)
        return context

    def is_allowed(self, permissions):
        return False

    @method_decorator(auth.decorators.login_required)
    def dispatch(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, pk=course_id)

        permissions = CoursePermissions()

        for membership in Membership.objects.filter(course=course, user=request.user):
            if membership.role == Membership.STUDENT:
                permissions.set_student(course.student_own_solutions_access, course.student_all_solutions_access)
            elif membership.role == Membership.TEACHER:
                permissions.set_teacher()

        if request.user.is_staff:
            permissions.set_admin()

        if not course.enable_sheet:
            permissions.sheet = False

        self.course = course
        self.permissions = permissions

        if not self.is_allowed(permissions):
            raise PermissionDenied()
        return super(BaseCourseView, self).dispatch(request, course, *args, **kwargs)


class CourseInfoView(BaseCourseView):
    tab = 'info'
    template_name = 'courses/info.html'

    def is_allowed(self, permissions):
        return permissions.info

    def get(self, request, course):
        solutions = Solution.objects.all()\
            .filter(coursesolution__course=course)\
            .order_by('reception_time')

        activity_data = [
            (calendar.timegm(solution.reception_time.timetuple()) * 1000, i + 1)
            for i, solution in enumerate(solutions)
        ]
        activity_data_json = json.dumps(activity_data)
        show_activity_plot = (len(activity_data) > 0)
        return render(request, self.template_name, self.get_context_data(activity_data_json=activity_data_json, show_activity_plot=show_activity_plot))


class StudentProblemResult(object):
    def __init__(self, short_name, complexity, points, max_points, criteria):
        self.short_name = short_name
        self.complexity = complexity
        self.points = points
        self.max_points = max_points
        self.criteria = criteria
        self.submitted = (points > 0)

    def is_full_solution(self):
        return self.points == self.max_points


class StudentResult(object):
    def __init__(self, name, surname, insubgroup, problemresults):
        self.name = name
        self.surname = surname
        self.insubgroup = insubgroup
        self.problemresults = problemresults
        self.summary = 0


class CourseSheetView(BaseCourseView):
    tab = 'sheet'
    template_name = 'courses/sheet.html'

    def is_allowed(self, permissions):
        return permissions.sheet

    def get(self, request, course):
        data = make_course_results(course)
        context = self.get_context_data(data=data)
        return render(request, self.template_name, context)


class CourseSheetEditView(BaseCourseView):
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
            for k, v in form.cleaned_data.iteritems():
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
        form = SolutionForm(
            data=data,
            files=files,
            problem_choices=self._make_choices(),
            compiler_queryset=self.course.compilers,
            initial=self._make_initial(),
        )
        return form

    def get(self, request, course):
        form = self._make_form()
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course):
        form = self._make_form(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                # remember used compiler to select it again later
                userprofile = request.user.userprofile
                userprofile.last_used_compiler = form.cleaned_data['compiler']
                userprofile.save()

                solution = new_solution(
                    request,
                    form.cleaned_data['compiler'],
                    form.cleaned_data['text'],
                    form.cleaned_data['upload'],
                    problem_id=form.cleaned_data['problem']
                )
                CourseSolution.objects.create(solution=solution, course=course)
                judge(solution)

            return redirect('courses:course_submission', course.id, solution.id)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


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

        problems = topic.list_problems()

        context = self.get_context_data()
        topics = course.topic_set.all()
        context['navigate_topics'] = True
        context['topics'] = topics
        context['active_topic'] = topic
        context['problems'] = problems
        return render(request, self.template_name, context)


def _locate_in_list(lst, x):
    try:
        pos = lst.index(x)
    except ValueError:
        return None
    length = len(lst)
    return ((pos + length - 1) % length, pos, (pos + 1) % length)


class CourseProblemsTopicProblemView(ProblemStatementMixin, BaseCourseView):
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
            context['statement'] = self.make_statement(problem)

            context['topics'] = course.topic_set.all()
            context['active_topic'] = topic
            return render(request, self.template_name, context)

        # fallback
        return redirect('courses:course_problems', course_id=course.id)


class CourseProblemsProblemView(ProblemStatementMixin, BaseCourseView):
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

        return False

    def get(self, request, course, problem_id, filename):
        problem = get_object_or_404(Problem, pk=problem_id)

        if self.is_aux_file(filename):
            return self.serve_aux_file(request, problem.id, filename)

        context = self.get_context_data()
        context['navigate_topics'] = False
        context['statement'] = self.make_statement(problem)
        return render(request, self.template_name, context)


AssignmentDataRepresentation = namedtuple('AssignmentDataRepresentation', 'topics extra_form')
TopicRepresentation = namedtuple('TopicRepresentation', 'topic_id name slots')
SlotRepresentation = namedtuple('SlotRepresentation', 'slot_id form is_penalty extra_requirements')


def create_assignment_form(membership, topic, post_data, slot=None, assignment=None):
    prefix = ''  # form prefix to distinguish forms on page
    if slot is not None:
        prefix = 'm{0}t{1}s{2}'.format(membership.id, topic.id, slot.id)
    elif assignment is not None:
        prefix = 'm{0}t{1}a{2}'.format(membership.id, topic.id, assignment.id)
    else:
        prefix = 'm{0}t{1}new'.format(membership.id, topic.id)

    form = ProblemAssignmentForm(data=post_data, instance=assignment, prefix=prefix)

    # Prepare for form validation
    form.fields['problem'].queryset = topic.list_problems()

    widget = form.fields['problem'].widget
    widget.attrs.update({'data-topic': topic.id})  # to use from JS

    form.fields['criteria'].queryset = topic.criteria

    return form


def prepare_assignment(course, membership, new_penalty_topic=None, post_data=None):
    topic_reprs = []
    topics = course.topic_set.all()
    for topic in topics:
        slot_reprs = []

        for slot in topic.slot_set.all():
            assignment = Assignment.objects.filter(membership=membership, topic=topic, slot=slot).first()
            form = create_assignment_form(
                membership=membership,
                topic=topic,
                post_data=post_data,
                slot=slot,
                assignment=assignment,
            )
            extra_requirements = (assignment and assignment.extra_requirements) or ''
            slot_reprs.append(SlotRepresentation(slot.id, form, False, extra_requirements))

        penalty_assignments = Assignment.objects.filter(membership=membership, topic=topic, slot=None)
        for assignment in penalty_assignments:
            form = create_assignment_form(
                membership=membership,
                topic=topic,
                post_data=post_data,
                assignment=assignment,
            )
            slot_reprs.append(SlotRepresentation(None, form, True, assignment.extra_requirements))

        if new_penalty_topic == topic.id:
            form = create_assignment_form(
                membership=membership,
                topic=topic,
                post_data=post_data,
            )
            slot_reprs.append(SlotRepresentation(None, form, True, ''))

        topic_reprs.append(TopicRepresentation(topic.id, topic.name, slot_reprs))

    extra_form = AddExtraProblemSlotForm()
    extra_form.fields['penaltytopic'].queryset = topics
    return AssignmentDataRepresentation(topic_reprs, extra_form)


class CourseAssignView(BaseCourseView):
    tab = 'assign'
    template_name = 'courses/assign.html'

    def is_allowed(self, permissions):
        return permissions.assign

    def _extract_new_penalty_topic(self, request):
        value = request.GET.get('penaltytopic')
        return int(value) if value is not None else None

    def get_context_data(self, **kwargs):
        context = super(CourseAssignView, self).get_context_data(**kwargs)
        context['criterion_cache'] = AllObjectsCache(Criterion)
        return context

    def get(self, request, course, membership_id=None):
        if membership_id is not None:
            membership = get_object_or_404(Membership, id=membership_id, course=course)
            ass = prepare_assignment(course, membership, self._extract_new_penalty_topic(request))
        else:
            # 'no selected user' empty view
            membership = None
            ass = None

        membership_form = SolutionListMemberForm(initial={'membership': membership}, queryset=course.get_student_memberships())

        context = self.get_context_data(data=ass, membership_form=membership_form)
        return render(request, self.template_name, context)

    def post(self, request, course, membership_id):
        membership = get_object_or_404(Membership, id=membership_id, course=course)
        membership_form = SolutionListMemberForm(initial={'membership': membership}, queryset=course.get_student_memberships())

        adr = prepare_assignment(course, membership, self._extract_new_penalty_topic(request), post_data=request.POST)

        all_valid = True

        for topic in adr.topics:
            for slot in topic.slots:
                if not slot.form.is_valid():
                    all_valid = False

        if all_valid:
            with transaction.atomic():
                for topic in adr.topics:
                    for slot in topic.slots:
                        form = slot.form
                        assignment = form.save(commit=False)
                        assignment.membership = membership
                        assignment.topic_id = topic.topic_id
                        assignment.slot_id = slot.slot_id
                        assignment.save()
                        form.save_m2m()

                        if slot.is_penalty and assignment.problem is None:
                            assignment.delete()

            #messages.add_message(request, messages.INFO, 'Hello world.')
            return redirect('courses:course_assignment', course_id=course.id, membership_id=membership_id)

        context = self.get_context_data(data=adr, membership_form=membership_form)
        return render(request, self.template_name, context)


def assignment_redirect_view(request, course_id):
    '''
    This view does not checks permissions because it does not retrieve any data from DB.
    It is safe but useless.
    '''
    membership_id = request.GET.get('membership')
    try:
        if not membership_id:
            return redirect('courses:course_assignment_empty', course_id)
        else:
            return redirect('courses:course_assignment', course_id, membership_id)
    except NoReverseMatch as e:
        raise Http404(e)


class CourseListView(StaffMemberRequiredMixin, generic.ListView):
    model = Course


class CourseCreateView(StaffMemberRequiredMixin, generic.CreateView):
    model = Course
    fields = ['name']

    def form_valid(self, form):
        with transaction.atomic():
            result = super(CourseCreateView, self).form_valid(form)
            course = self.object
            course.compilers = Compiler.objects.filter(legacy=False)
            return result


class CourseStandingsView(BaseCourseView):
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

    def get_success_url(self):
        return reverse('courses:criterion_index')


'''
Solutions list
'''


class CourseAllSolutionsView(BaseCourseView):
    tab = 'all_solutions'
    template_name = 'courses/solutions.html'
    paginate_by = 12

    def is_allowed(self, permissions):
        return permissions.all_solutions

    def get(self, request, course):
        # filters
        membership = None
        problem_id = None

        memberships = course.get_student_memberships()
        membership_form = SolutionListMemberForm(data=request.GET, queryset=memberships)
        if membership_form.is_valid():
            membership = membership_form.cleaned_data['membership']

        if membership is not None:
            problem_form = SolutionListProblemForm(data=request.GET, problem_choices=make_problem_choices(course, membership_id=membership.id))
        else:
            problem_form = SolutionListProblemForm(data=request.GET, problem_choices=make_problem_choices(course, full=True))
        if problem_form.is_valid():
            problem_id = problem_form.cleaned_data['problem']

        solutions = Solution.objects.all()\
            .filter(coursesolution__course=course)\
            .prefetch_related('compiler')\
            .select_related('author', 'problem', 'source_code', 'best_judgement')\
            .order_by('-reception_time', 'id')

        if membership is not None:
            solutions = solutions.filter(author=membership.user)

        if problem_id is not None:
            solutions = solutions.filter(problem_id=problem_id)

        context = paginate(request, solutions, self.paginate_by)

        context['membership_form'] = membership_form
        context['problem_form'] = problem_form

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
    paginate_by = 12

    def is_allowed(self, permissions):
        return permissions.my_solutions

    def get(self, request, course):
        problem_form = SolutionListProblemForm(data=request.GET, problem_choices=make_problem_choices(course, user_id=request.user.id))
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

        # tune visual representation for better fitting screen width
        context['show_author'] = False  # all solutions belong to the same author
        context['show_compilerbox'] = False
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
        return permissions.my_problems

    def get(self, request, course):
        membership = get_object_or_404(Membership, course=course, user=request.user, role=Membership.STUDENT)
        user_result = make_course_single_result(course, membership, request.user)
        context = self.get_context_data(user_result=user_result)
        return render(request, self.template_name, context)

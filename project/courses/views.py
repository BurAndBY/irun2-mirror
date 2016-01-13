# -*- coding: utf-8 -*-

from collections import namedtuple

from django.contrib import auth
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.decorators import method_decorator
from django.views import generic
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from forms import SolutionForm, ProblemAssignmentForm, AddExtraProblemSlotForm, SolutionListUserForm, SolutionListProblemForm, ActivityRecordFakeForm
from models import Course, Topic, Membership, Assignment, Criterion, CourseSolution, Activity, ActivityRecord
from services import make_problem_choices, make_course_results

from common.constants import EMPTY_SELECT
from common.pageutils import paginate
from common.cacheutils import AllObjectsCache
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
            'active_tab': self.tab,
            'active_subtab': self.subtab,
        }
        context.update(kwargs)
        return context

    @method_decorator(auth.decorators.login_required)
    def dispatch(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, pk=course_id)
        self.course = course
        return super(BaseCourseView, self).dispatch(request, course, *args, **kwargs)


class CourseInfoView(BaseCourseView):
    tab = 'info'
    template_name = 'courses/info.html'

    def get(self, request, course_id):
        return render(request, self.template_name, self.get_context_data())


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

    def get(self, request, course):
        data = make_course_results(course)
        context = self.get_context_data(data=data)
        return render(request, self.template_name, context)


class CourseSheetEditView(BaseCourseView):
    tab = 'sheet'
    template_name = 'courses/sheet.html'

    def get(self, request, course):
        data = make_course_results(course)
        context = self.get_context_data(data=data, edit_mode=True, choices=ActivityRecord.CHOICES)
        return render(request, self.template_name, context)


class CourseSheetEditApiView(BaseCourseView):
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

    def _make_choices(self):
        return make_problem_choices(self.course, full=True)

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
                    request.user,
                    form.cleaned_data['compiler'],
                    form.cleaned_data['text'],
                    form.cleaned_data['upload'],
                    problem_id=form.cleaned_data['problem']
                )
                CourseSolution.objects.create(solution=solution, course=course)
                judge(solution)

            return redirect('courses:show_course_info', course.id)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


'''
Problems
'''


class CourseProblemsView(BaseCourseView):
    tab = 'problems'
    template_name = 'courses/problems_base.html'

    def get(self, request, course):
        topics = course.topic_set.all()

        context = self.get_context_data(topics=topics)
        return render(request, self.template_name, context)


class CourseProblemsTopicView(BaseCourseView):
    tab = 'problems'
    template_name = 'courses/problems_list.html'

    def get(self, request, course, topic_id):
        topic = course.topic_set.filter(id=topic_id).first()
        if topic is None:
            return redirect('courses:course_problems', course_id=course.id)

        problems = topic.list_problems()

        context = self.get_context_data()
        topics = course.topic_set.all()
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


class CourseProblemsTopicProblemView(BaseCourseView, ProblemStatementMixin):
    tab = 'problems'
    template_name = 'courses/problems_statement.html'

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

    def _extract_new_penalty_topic(self, request):
        value = request.GET.get('penaltytopic')
        return int(value) if value is not None else None

    def get_context_data(self, **kwargs):
        context = super(CourseAssignView, self).get_context_data(**kwargs)
        context['criterion_cache'] = AllObjectsCache(Criterion)
        return context

    def get(self, request, course, membership_id):
        membership = get_object_or_404(Membership, id=membership_id, course=course)

        ass = prepare_assignment(course, membership, self._extract_new_penalty_topic(request))

        context = self.get_context_data(data=ass)
        return render(request, self.template_name, context)

    def post(self, request, course, membership_id):
        membership = get_object_or_404(Membership, id=membership_id, course=course)

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

        context = self.get_context_data(data=adr)
        return render(request, self.template_name, context)


class CourseListView(generic.ListView):
    model = Course


class CourseCreateView(generic.CreateView):
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
    template_name = 'courses/standings2.html'

    def get(self, request, course):
        context = self.get_context_data()
        res = make_course_results(course)
        context['course_descr'] = res.course_descr
        context['results'] = res.user_results
        return render(request, self.template_name, context)


'''
Criterion
'''


class CriterionListView(generic.ListView):
    model = Criterion


class CriterionCreateView(generic.CreateView):
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

    def get(self, request, course):
        # filters
        user_id = None
        problem_id = None

        users = course.members.order_by('last_name', 'first_name', 'id')
        user_choices = tuple([(None, EMPTY_SELECT)] + [(user.id, user.get_full_name()) for user in users])
        user_form = SolutionListUserForm(data=request.GET, user_choices=user_choices)
        if user_form.is_valid():
            user_id = user_form.cleaned_data['user']

        if user_id is not None:
            problem_form = SolutionListProblemForm(data=request.GET, problem_choices=make_problem_choices(course, user_id=user_id))
        else:
            problem_form = SolutionListProblemForm(data=request.GET, problem_choices=make_problem_choices(course, full=True))
        if problem_form.is_valid():
            problem_id = problem_form.cleaned_data['problem']

        solutions = Solution.objects.all()\
            .filter(coursesolution__course=course)\
            .prefetch_related('compiler')\
            .select_related('source_code', 'best_judgement')\
            .order_by('-reception_time', 'id')

        if user_id is not None:
            solutions = solutions.filter(author_id=user_id)

        if problem_id is not None:
            solutions = solutions.filter(problem_id=problem_id)

        context = paginate(request, solutions, self.paginate_by)

        context['user_form'] = user_form
        context['problem_form'] = problem_form
        context['show_author'] = True
        context = self.get_context_data(**context)
        return render(request, self.template_name, context)


class CourseMySolutionsView(BaseCourseView):
    tab = 'my_solutions'
    template_name = 'courses/solutions.html'
    paginate_by = 12

    def get(self, request, course):
        problem_form = SolutionListProblemForm(data=request.GET, problem_choices=make_problem_choices(course, user_id=request.user.id))
        if problem_form.is_valid():
            problem_id = problem_form.cleaned_data['problem']
        else:
            problem_id = None

        solutions = Solution.objects.all()\
            .filter(coursesolution__course=course, author=request.user)\
            .prefetch_related('compiler')\
            .select_related('source_code', 'best_judgement')\
            .order_by('-reception_time', 'id')

        if problem_id is not None:
            solutions = solutions.filter(problem_id=problem_id)

        context = paginate(request, solutions, self.paginate_by)
        context['problem_form'] = problem_form
        context['show_author'] = False  # all solutions belong to the same author
        context = self.get_context_data(**context)
        return render(request, self.template_name, context)

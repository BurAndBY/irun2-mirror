from collections import namedtuple

from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from problems.models import (
    Problem,
    ProblemFolder,
    ProblemRelatedFile,
)
from problems.views import ProblemStatementMixin

from courses.services import (
    get_assigned_problem_set,
    get_simple_assignments,
)
from courses.views import BaseCourseView
from courses.models import (
    Assignment,
    Course,
    CourseSolution,
    TopicCommonProblem,
)


EditorialFile = namedtuple('EditorialFile', 'filename description')
DirectoryLocation = namedtuple('DirectoryLocation', ['prev_url', 'cur_position', 'folder_url', 'next_url', 'total_positions'])


def _locate_in_list(lst, x):
    try:
        pos = lst.index(x)
    except ValueError:
        return None
    length = len(lst)
    return ((pos + length - 1) % length, pos, (pos + 1) % length)


class TopicHeader(object):
    def __init__(self, course):
        self.topics = course.topic_set.all()

        self.active_topic_id = None
        self.is_common_topic_active = False


'''
Mixins
'''


class EmptyProblemsMixin(object):
    def get_problem_ids(self):
        return []

    def get_folder_url(self):
        raise NotImplementedError()

    def get_problem_url(self, problem_id):
        raise NotImplementedError()


class CommonProblemsMixin(object):
    def get_problem_ids(self):
        return Course.common_problems.through.objects.\
            filter(course=self.course).\
            order_by('pk').\
            values_list('problem_id', flat=True)

    def get_folder_url(self):
        return reverse('courses:course_common_problems', args=(self.course.id,))

    def get_problem_url(self, problem_id):
        return reverse('courses:course_common_problems_problem', args=(self.course.id, problem_id))


class TopicCommonProblemsMixin(object):
    def get_problem_ids(self):
        return TopicCommonProblem.objects.filter(topic__course=self.course, topic_id=self.topic_id).\
            order_by('pk').\
            values_list('problem_id', flat=True)

    def get_folder_url(self):
        return reverse('courses:course_problems_topic', args=(self.course.id, self.topic_id))

    def get_problem_url(self, problem_id):
        return reverse('courses:course_problems_topic_common_problem', args=(self.course.id, self.topic_id, problem_id))


class TopicProblemsMixin(object):
    def get_problem_ids(self):
        return Problem.objects.filter(folders__topic__course=self.course, folders__topic__id=self.topic_id).\
            exclude(folders__topic=None).\
            values_list('pk', flat=True)

    def get_folder_url(self):
        return reverse('courses:course_problems_topic', args=(self.course.id, self.topic_id))

    def get_problem_url(self, problem_id):
        return reverse('courses:course_problems_topic_problem', args=(self.course.id, self.topic_id, problem_id))


class BaseProblemView(BaseCourseView):
    tab = 'problems'
    template_name = 'courses/problems_base.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topic_header'] = TopicHeader(self.course)
        return context

    def is_allowed(self, permissions):
        return permissions.problems


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


'''
Topic
'''


class RealTopicMixin(object):
    @property
    def topic_id(self):
        return int(self.kwargs['topic_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topic_header'].active_topic_id = self.topic_id
        return context


class CommonTopicMixin(object):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topic_header'].is_common_topic_active = True
        return context


'''
List vs Item
'''


class ListMixin(object):
    template_name = 'courses/problems_list.html'
    main_cls = object
    common_cls = object

    def get(self, request, course, *args, **kwargs):
        main_problem_ids = self.main_cls.get_problem_ids(self)
        common_problem_ids = self.common_cls.get_problem_ids(self)

        problems = Problem.objects.filter(pk__in=set(main_problem_ids) | set(common_problem_ids)).in_bulk()

        assigned_problems = get_assigned_problem_set(course)

        context = self.get_context_data(
            problems=self._load(problems, assigned_problems, main_problem_ids, self.main_cls),
            common_problems=self._load(problems, set(), common_problem_ids, self.common_cls),
        )
        return render(request, self.template_name, context)

    def _load(self, problems, assigned_problems, ids, cls):
        problems_with_assign_flag = []
        for pk in ids:
            problem = problems.get(pk)
            if problem is None:
                continue
            assigned = (pk in assigned_problems)
            problems_with_assign_flag.append((problem, assigned, cls.get_problem_url(self, pk)))
        return problems_with_assign_flag


class ItemMixin(CourseStatementMixin, ProblemStatementMixin):
    template_name = 'courses/problems_statement.html'

    def get(self, request, course, *args, **kwargs):
        problem_ids = list(self.get_problem_ids())
        problem_id = int(self.kwargs['problem_id'])

        positions = _locate_in_list(problem_ids, problem_id)
        if positions is None:
            return redirect(self.get_folder_url())

        filename = self.kwargs.get('filename')
        if self.is_aux_file(filename):
            return self.serve_aux_file(request, problem_id, filename)

        try:
            problem = Problem.objects.get(pk=problem_id)
        except Problem.DoesNotExist:
            return redirect(self.get_folder_url())
        self.problem = problem

        prv, cur, nxt = positions
        location = DirectoryLocation(
            prev_url=self.get_problem_url(problem_ids[prv]),
            cur_position=cur + 1,  # 1-based
            folder_url=self.get_folder_url(),
            next_url=self.get_problem_url(problem_ids[nxt]),
            total_positions=len(problem_ids),
        )

        context = self.get_context_data(
            location=location,
            problem=problem,
            statement=self.make_statement(problem),
        )
        return render(request, self.template_name, context)


'''
Views
'''


class EmptyView(BaseProblemView):
    def get(self, request, course):
        context = self.get_context_data()
        return render(request, self.template_name, context)


class FullTopicListView(RealTopicMixin, ListMixin, BaseProblemView):
    main_cls = TopicProblemsMixin
    common_cls = TopicCommonProblemsMixin


class TopicItemView(RealTopicMixin, ItemMixin, TopicProblemsMixin, BaseProblemView):
    pass


class TopicCommonProblemsItemView(RealTopicMixin, ItemMixin, TopicCommonProblemsMixin, BaseProblemView):
    pass


class CommonProblemsListView(CommonTopicMixin, ListMixin, BaseProblemView):
    main_cls = EmptyProblemsMixin
    common_cls = CommonProblemsMixin


class CommonProblemsItemView(CommonTopicMixin, ItemMixin, CommonProblemsMixin, BaseProblemView):
    pass


class AnyProblemView(CourseStatementMixin, ProblemStatementMixin, BaseCourseView):
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

    def get(self, request, course, problem_id, filename=None):
        problem = get_object_or_404(Problem, pk=problem_id)
        self.problem = problem

        if self.is_aux_file(filename):
            return self.serve_aux_file(request, problem.id, filename)

        context = self.get_context_data(
            problem=problem,
            statement=self.make_statement(problem),
        )
        return render(request, self.template_name, context)

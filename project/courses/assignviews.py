from collections import namedtuple

from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.decorators import method_decorator

from common.networkutils import never_ever_cache
from problems.models import Problem

from courses.forms import AddExtraProblemSlotForm
from courses.models import (
    Assignment,
    Membership,
    Slot,
    Topic,
)
from courses.views import (
    BaseCourseView,
    UserCacheMixinMixin,
)
from courses.services import make_course_single_result


AssignmentDataRepresentation = namedtuple('AssignmentDataRepresentation', 'topic_reprs')
TopicRepresentation = namedtuple('TopicRepresentation', 'topic_result')
ProblemRepresentation = namedtuple('ProblemRepresentation', 'problem used used_by_others used_by_me')


class BaseCourseAssignView(BaseCourseView):
    def is_allowed(self, permissions):
        return permissions.assign


class CourseEmptyAssignView(UserCacheMixinMixin, BaseCourseAssignView):
    tab = 'assign'
    template_name = 'courses/assign.html'

    def get(self, request, course):
        context = self.get_context_data()
        context['student_list'] = self.get_user_cache().list_students()
        return render(request, self.template_name, context)


class BaseCourseMemberAssignView(UserCacheMixinMixin, BaseCourseAssignView):
    def get_context_data(self, **kwargs):
        context = super(BaseCourseMemberAssignView, self).get_context_data(**kwargs)
        user_cache = self.get_user_cache()
        context['student_list'] = user_cache.list_students()
        context['current_student'] = user_cache.get_user(self.membership.user_id)
        return context

    def dispatch(self, request, course_id, user_id, *args, **kwargs):
        membership = Membership.objects.filter(user_id=user_id, course_id=course_id, role=Membership.STUDENT).first()
        if membership is None:
            return redirect('courses:assignment:empty', course_id)
        self.membership = membership
        return super(BaseCourseMemberAssignView, self).dispatch(request, course_id, membership, *args, **kwargs)


class CourseAssignView(BaseCourseMemberAssignView):
    tab = 'assign'
    template_name = 'courses/assign.html'

    @method_decorator(never_ever_cache)
    def get(self, request, course, membership):
        user_result = make_course_single_result(course, membership)

        topic_reprs = []
        for topic_result in user_result.topic_results:
            topic_repr = TopicRepresentation(topic_result)
            topic_reprs.append(topic_repr)

        assignment_repr = AssignmentDataRepresentation(topic_reprs)

        extra_form = AddExtraProblemSlotForm()
        extra_form.fields['penaltytopic'].queryset = course.topic_set.all()

        context = self.get_context_data(data=assignment_repr, extra_form=extra_form,
                                        common_problem_results=user_result.common_problem_results, user_id=membership.user_id)
        return render(request, self.template_name, context)


class CourseAssignCreatePenaltyProblem(BaseCourseMemberAssignView):
    def post(self, request, course, membership):
        extra_form = AddExtraProblemSlotForm(request.POST)
        extra_form.fields['penaltytopic'].queryset = course.topic_set.all()
        if extra_form.is_valid():
            topic = extra_form.cleaned_data['penaltytopic']
            Assignment.objects.create(topic=topic, membership=membership)
        return redirect('courses:assignment:index', course.id, membership.user_id)


class CourseAssignDeletePenaltyProblem(BaseCourseMemberAssignView):
    def post(self, request, course, membership, assignment_id):
        Assignment.objects.filter(pk=assignment_id, membership=membership).delete()
        return redirect('courses:assignment:index', course.id, membership.user_id)


AssignmentData = namedtuple('AssignmentData', 'topic assignment')


def _get_assignment_data(request, course, membership):
    '''
    Returns assignment together with related data.
    '''
    topic_id = request.POST.get('topic')
    if topic_id is None:
        raise Http404('no topic id provided')

    topic = get_object_or_404(Topic, pk=topic_id, course=course)

    slot_id = request.POST.get('slot')
    if slot_id is not None:
        if not Slot.objects.filter(pk=slot_id, topic=topic).exists():
            raise Http404('wrong slot for topic')

    created = False

    if slot_id is not None:
        # this is normal problem
        assignment, created = Assignment.objects.get_or_create(slot_id=slot_id, topic=topic, membership=membership)
    else:
        # this is penalty problem: assignment id is required!
        assignment_id = request.POST.get('assignment')
        if assignment_id is None:
            raise Http404('no assignment id passed')
        assignment = get_object_or_404(Assignment, pk=assignment_id, topic=topic, membership=membership)

    return AssignmentData(topic, assignment)


class CourseAssignProblemApiView(BaseCourseMemberAssignView):
    template_name = 'courses/api_slotresult.html'

    def post(self, request, course, membership):
        adata = _get_assignment_data(request, course, membership)

        problem_id = request.POST.get('problem')  # integer as string or None
        if problem_id is not None:
            if adata.topic.problem_folder is None:
                raise Http404('no problems are available for the topic')
            if not adata.topic.problem_folder.problem_set.filter(pk=problem_id).exists():
                raise Http404('problem does not exist in the topic folder')

        assignment = adata.assignment
        assignment.problem_id = problem_id
        assignment.save()

        user_result = make_course_single_result(course, membership)
        context = {
            'slot_result': user_result.get_slot_result(assignment),
            'course_id': course.id,
            'permissions': self.permissions,
        }
        return render(request, self.template_name, context)


class CourseAssignCriterionApiView(BaseCourseMemberAssignView):
    def post(self, request, course, membership):
        adata = _get_assignment_data(request, course, membership)

        criterion_id = request.POST.get('criterion')  # integer as string or None

        ok = request.POST.get('ok')  # '0' or '1'
        try:
            ok = bool(int(ok))
        except ValueError:
            raise Http404('ok or not ok is not set')

        if criterion_id is not None:
            assignment = adata.assignment
            if ok:
                if not assignment.criteria.filter(pk=criterion_id).exists():
                    assignment.criteria.add(criterion_id)
                result = True
            else:
                assignment.criteria.remove(criterion_id)
                result = False

            return JsonResponse({'ok': int(result)})

        else:
            return JsonResponse()


class ListTopicProblemsApiView(BaseCourseMemberAssignView):
    template_name = 'courses/api_list_problems.html'

    @method_decorator(never_ever_cache)
    def get(self, request, course, membership, topic_id):
        problem_reprs = []
        topic = Topic.objects.filter(pk=topic_id, course=course).first()

        if topic is not None and topic.problem_folder_id is not None:
            used_by_others = set()
            used_by_me = set()

            for membership_id, problem_id in Assignment.objects.\
                    filter(membership__course=course, membership__role=Membership.STUDENT).\
                    values_list('membership_id', 'problem_id'):
                (used_by_me if membership_id == membership.id else used_by_others).add(problem_id)

            for problem in Problem.objects.filter(folders__id=topic.problem_folder_id):
                by_others = problem.id in used_by_others
                by_me = problem.id in used_by_me
                problem_reprs.append(ProblemRepresentation(problem, by_others or by_me, by_others, by_me))

        context = {'problem_reprs': problem_reprs, 'course_id': course.id}
        return render(request, self.template_name, context)

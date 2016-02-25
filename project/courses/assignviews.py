from collections import namedtuple

from django.db.models import F
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.decorators import method_decorator

from forms import AddExtraProblemSlotForm
from models import Topic, Membership, Assignment, Slot
from services import make_course_single_result

from common.networkutils import never_ever_cache
from problems.models import Problem

from .views import BaseCourseView


AssignmentDataRepresentation = namedtuple('AssignmentDataRepresentation', 'topic_reprs')
TopicRepresentation = namedtuple('TopicRepresentation', 'topic_result problem_reprs')
ProblemRepresentation = namedtuple('ProblemRepresentation', 'problem used')


class BaseCourseAssignView(BaseCourseView):
    def is_allowed(self, permissions):
        return permissions.assign


class CourseEmptyAssignView(BaseCourseAssignView):
    tab = 'assign'
    template_name = 'courses/assign.html'

    def get(self, request, course):
        context = self.get_context_data()
        context['student_list'] = self.get_user_cache().list_students()
        return render(request, self.template_name, context)


class BaseCourseMemberAssignView(BaseCourseAssignView):
    def get_context_data(self, **kwargs):
        context = super(BaseCourseMemberAssignView, self).get_context_data(**kwargs)
        user_cache = self.get_user_cache()
        context['student_list'] = user_cache.list_students()
        context['current_student'] = user_cache.get_user(self.membership.user_id)
        return context

    def dispatch(self, request, course_id, user_id, *args, **kwargs):
        membership = get_object_or_404(Membership, user_id=user_id, course_id=course_id, role=Membership.STUDENT)
        self.membership = membership
        return super(BaseCourseMemberAssignView, self).dispatch(request, course_id, membership, *args, **kwargs)


class CourseAssignView(BaseCourseMemberAssignView):
    tab = 'assign'
    template_name = 'courses/assign.html'

    @method_decorator(never_ever_cache)
    def get(self, request, course, membership):
        user_result = make_course_single_result(course, membership)

        used_problems = {}
        for topic_id, problem_id in Assignment.objects.\
                filter(membership__course=course, membership__role=Membership.STUDENT).\
                exclude(membership=membership).\
                values_list('topic_id', 'problem_id'):
            used_problems.setdefault(topic_id, set()).add(problem_id)

        # find out what problem folders do we need
        folder_ids = set()
        for topic_result in user_result.topic_results:
            topic = topic_result.topic_descr.topic
            if topic.problem_folder_id is not None:
                folder_ids.add(topic.problem_folder_id)

        folder_id_to_problems = {}
        for problem in Problem.objects.filter(folders__id__in=folder_ids).annotate(folder_id=F('folders__id')):
            folder_id_to_problems.setdefault(problem.folder_id, []).append(problem)
        assert None not in folder_id_to_problems

        topic_reprs = []
        for topic_result in user_result.topic_results:
            topic = topic_result.topic_descr.topic

            used_topic_problems = used_problems.get(topic.id, set())

            problem_reprs = []
            for problem in folder_id_to_problems.get(topic.problem_folder_id):
                used = problem.id in used_topic_problems
                problem_reprs.append(ProblemRepresentation(problem, used))

            topic_repr = TopicRepresentation(topic_result, problem_reprs)
            topic_reprs.append(topic_repr)

        assignment_repr = AssignmentDataRepresentation(topic_reprs)

        extra_form = AddExtraProblemSlotForm()
        extra_form.fields['penaltytopic'].queryset = course.topic_set.all()

        context = self.get_context_data(data=assignment_repr, extra_form=extra_form, common_problem_results=user_result.common_problem_results)
        return render(request, self.template_name, context)


class CourseAssignCreatePenaltyProblem(BaseCourseMemberAssignView):
    def post(self, request, course, membership):
        extra_form = AddExtraProblemSlotForm(request.POST)
        extra_form.fields['penaltytopic'].queryset = course.topic_set.all()
        if extra_form.is_valid():
            topic = extra_form.cleaned_data['penaltytopic']
            Assignment.objects.create(topic=topic, membership=membership)
        return redirect('courses:course_assignment', course.id, membership.user_id)


class CourseAssignDeletePenaltyProblem(BaseCourseMemberAssignView):
    def post(self, request, course, membership, assignment_id):
        Assignment.objects.filter(pk=assignment_id, membership=membership).delete()
        return redirect('courses:course_assignment', course.id, membership.user_id)


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
            'course_id': course.id
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

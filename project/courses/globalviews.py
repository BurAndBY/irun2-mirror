from collections import namedtuple

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.views import generic
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _

from cauth.mixins import (
    LoginRequiredMixin,
    AdminMemberRequiredMixin,
)
from common.education.year import make_academic_year_string
from proglangs.models import Compiler

from courses.models import (
    Course,
    CourseSolution,
    CourseStatus,
    Membership,
)
from courses.forms import NewCourseForm
from courses.messaging import MessageCountManager


'''
List of courses
'''

CourseListItem = namedtuple('CourseListItem', 'id name my student_count solution_count unread_count unresolved_count archived')


class BaseCourseListView(generic.TemplateView):
    template_name = 'courses/course_list.html'

    def _all_courses_queryset(self, user):
        if user.is_staff:
            return Course.objects.all()
        if user.is_admin:
            return Course.objects.filter(Q(owner__users=user) | Q(membership__user=user)).distinct()
        return Course.objects.none()

    def _count_for_courses(self, qs):
        # {course_id -> count}
        result = {}
        for course_id, count in qs.values_list('course_id').annotate(total=Count('course_id')):
            result[course_id] = count
        return result

    def get(self, request):
        message_count_manager = MessageCountManager(user=request.user)
        my_courses = message_count_manager.my_course_ids()
        students_per_course = self._count_for_courses(Membership.objects.filter(role=Membership.STUDENT))
        solutions_per_course = self._count_for_courses(CourseSolution.objects.all())

        year_to_courses = {}
        no_year_courses = []
        for course in self.get_queryset():
            pk = course.id
            message_counts = message_count_manager.get(pk)
            item = CourseListItem(
                pk,
                smart_text(course),
                pk in my_courses,
                students_per_course.get(pk, 0),
                solutions_per_course.get(pk, 0),
                message_counts.unread,
                message_counts.unresolved,
                course.status == CourseStatus.ARCHIVED
            )
            if course.academic_year is not None:
                year_to_courses.setdefault(course.academic_year, []).append(item)
            else:
                no_year_courses.append(item)

        pairs = []
        for academic_year, courses in sorted(year_to_courses.items(), reverse=True):
            pairs.append((make_academic_year_string(academic_year), courses))
        if no_year_courses:
            pairs.append((None, no_year_courses))

        context = self.get_context_data(pairs=pairs)
        return self.render_to_response(context)

    def get_queryset(self):
        raise NotImplementedError()


class ActiveCourseListView(AdminMemberRequiredMixin, BaseCourseListView):
    def get_queryset(self):
        return self._all_courses_queryset(self.request.user).filter(status=CourseStatus.RUNNING)

    def get_context_data(self, **kwargs):
        context = super(ActiveCourseListView, self).get_context_data(**kwargs)
        context['title'] = _('Active courses')
        context['link_to_all'] = True
        context['access_warning'] = True
        return context


class AllCourseListView(AdminMemberRequiredMixin, BaseCourseListView):
    def get_queryset(self):
        return self._all_courses_queryset(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(AllCourseListView, self).get_context_data(**kwargs)
        context['title'] = _('All courses')
        context['access_warning'] = True
        return context


class MyCourseListView(LoginRequiredMixin, BaseCourseListView):
    def get_queryset(self):
        return Course.objects.filter(membership__user=self.request.user).distinct()

    def get_context_data(self, **kwargs):
        context = super(MyCourseListView, self).get_context_data(**kwargs)
        context['title'] = _('My courses')
        return context


class CourseCreateView(AdminMemberRequiredMixin, generic.CreateView):
    model = Course
    form_class = NewCourseForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            result = super(CourseCreateView, self).form_valid(form)
            course = self.object
            course.compilers.set(Compiler.objects.filter(default_for_courses=True))
            return result

    def get_initial(self):
        # Creating a new course before the 1st of July 2016 => getting "2015-2016".
        # Creating a new course after the 1st of July 2016 => getting "2016-2017".
        today = timezone.now().date()
        if today.month <= 6:
            year = today.year - 1
        else:
            year = today.year

        return {'academic_year': year}

from collections import namedtuple

from django.db import transaction
from django.db.models import Count, F
from django.shortcuts import render
from django.utils import timezone
from django.views import generic
from django.utils.encoding import smart_text

from cauth.mixins import StaffMemberRequiredMixin
from proglangs.models import Compiler

from courses.models import Course, Membership, MailThread, CourseSolution
from courses.forms import NewCourseForm
from courses.utils import make_academic_year_string


'''
List of courses
'''

CourseListItem = namedtuple('CourseListItem', 'id name my student_count solution_count unread_count unresolved_count')


class CourseListView(StaffMemberRequiredMixin, generic.View):
    template_name = 'courses/course_list.html'

    def _count_for_courses(self, qs):
        # {course_id -> count}
        result = {}
        for course_id, count in qs.values_list('course_id').annotate(total=Count('course_id')):
            result[course_id] = count
        return result

    def get(self, request):
        my_courses = set(Membership.objects.filter(user=request.user).values_list('course_id', flat=True))
        students_per_course = self._count_for_courses(Membership.objects.filter(role=Membership.STUDENT))
        mail_threads_all_per_course = self._count_for_courses(MailThread.objects.all())
        mail_threads_read_per_course = self._count_for_courses(MailThread.objects.filter(
            mailuserthreadvisit__user=request.user,
            mailuserthreadvisit__timestamp__gte=F('last_message_timestamp')
        ))
        mail_threads_unresolved_per_course = self._count_for_courses(MailThread.objects.filter(
            resolved=False
        ))
        solutions_per_course = self._count_for_courses(CourseSolution.objects.all())

        year_to_courses = {}
        for course in Course.objects.all():
            pk = course.id
            item = CourseListItem(
                pk,
                smart_text(course),
                pk in my_courses,
                students_per_course.get(pk, 0),
                solutions_per_course.get(pk, 0),
                mail_threads_all_per_course.get(pk, 0) - mail_threads_read_per_course.get(pk, 0),
                mail_threads_unresolved_per_course.get(pk, 0),
            )
            year_to_courses.setdefault(course.academic_year, []).append(item)

        pairs = []
        for academic_year, courses in sorted(year_to_courses.items(), reverse=True):
            if academic_year is None:
                pairs.append((None, courses))
            else:
                pairs.append((make_academic_year_string(academic_year), courses))

        return render(request, self.template_name, {'pairs': pairs})


class CourseCreateView(StaffMemberRequiredMixin, generic.CreateView):
    model = Course
    form_class = NewCourseForm

    def form_valid(self, form):
        with transaction.atomic():
            result = super(CourseCreateView, self).form_valid(form)
            course = self.object
            course.compilers = Compiler.objects.filter(default_for_courses=True)
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

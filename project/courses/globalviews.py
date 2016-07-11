from django.db import transaction
from django.shortcuts import render
from django.utils import timezone
from django.views import generic

from cauth.mixins import StaffMemberRequiredMixin
from proglangs.models import Compiler

from courses.models import Course
from courses.forms import NewCourseForm
from courses.utils import make_academic_year_string

'''
List of courses
'''


class CourseListView(StaffMemberRequiredMixin, generic.View):
    template_name = 'courses/course_list.html'

    def get(self, request):
        year_to_courses = {}
        for course in Course.objects.all():
            year_to_courses.setdefault(course.academic_year, []).append(course)

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

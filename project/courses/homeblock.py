from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from home.registry import (
    HomePageBlock,
    HomePageBlockStyle,
    HomePageBlockFactory,
)

from courses.models import Course, CourseStatus
from courses.messaging import MessageCountManager


class CourseBlockFactory(HomePageBlockFactory):
    template = 'courses/homeblock.html'
    icon = 'education'

    def create_blocks(self, request):
        if request.user.is_authenticated:
            manager = MessageCountManager(request.user)
            my_courses = Course.objects.filter(pk__in=manager.my_course_ids())
            my_course_count = len(manager.my_course_ids())

            if my_course_count > 0:
                active_courses_with_unread = []
                for course in my_courses.filter(status=CourseStatus.RUNNING):  # default ordering
                    active_courses_with_unread.append((course, manager.get(course.id).unread))

                ctx = {
                    'my_course_count': my_course_count,
                    'my_active_courses': active_courses_with_unread
                }
                yield HomePageBlock(
                    style=HomePageBlockStyle.MY,
                    icon=self.icon,
                    name=_('My courses'),
                    count=my_course_count,
                    content=render_to_string(self.template, ctx)
                )

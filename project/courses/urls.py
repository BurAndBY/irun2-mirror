from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<course_id>[0-9]+)/$', views.ShowCourseInfoView.as_view(), name='show_course_info'),
    url(r'^(?P<course_id>[0-9]+)/standings/$', views.ShowCourseStandingsView.as_view(), name='show_course_standings'),
    url(r'^(?P<course_id>[0-9]+)/submit/$', views.ShowCourseSubmitView.as_view(), name='show_course_submit'),
]

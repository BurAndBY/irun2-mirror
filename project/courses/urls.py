from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<course_id>[0-9]+)/$', views.CourseInfoView.as_view(), name='show_course_info'),
    url(r'^(?P<course_id>[0-9]+)/standings/$', views.CourseStandingsView.as_view(), name='course_standings'),
    url(r'^(?P<course_id>[0-9]+)/sheet/$', views.CourseSheetView.as_view(), name='course_sheet'),
    url(r'^(?P<course_id>[0-9]+)/submit/$', views.CourseSubmitView.as_view(), name='show_course_submit'),

    url(r'^(?P<course_id>[0-9]+)/problemset/$', views.CourseProblemsView.as_view(), name='course_problems'),
    url(r'^(?P<course_id>[0-9]+)/problemset/(?P<topic_id>[0-9]+)/$', views.CourseProblemsTopicView.as_view(), name='course_problems_topic'),
    url(r'^(?P<course_id>[0-9]+)/problemset/(?P<topic_id>[0-9]+)/(?P<problem_id>[0-9]+)/(?P<filename>.+)?$', views.CourseProblemsTopicProblemView.as_view(), name='course_problems_topic_problem'),

    url(r'^(?P<course_id>[0-9]+)/settings/$', views.CourseSettingsPropertiesView.as_view(), name='course_settings_properties'),
    url(r'^(?P<course_id>[0-9]+)/settings/topics/$', views.CourseSettingsTopicsView.as_view(), name='course_settings_topics'),
    url(r'^(?P<course_id>[0-9]+)/settings/topics/create/$', views.CourseSettingsTopicsCreateView.as_view(), name='course_settings_topics_create'),
    url(r'^(?P<course_id>[0-9]+)/settings/topics/(?P<topic_id>[0-9]+)/$', views.CourseSettingsTopicsUpdateView.as_view(), name='course_settings_topics_update'),
    url(r'^(?P<course_id>[0-9]+)/settings/users/$', views.CourseSettingsUsersView.as_view(), name='course_settings_users'),
    url(r'^(?P<course_id>[0-9]+)/settings/compilers/$', views.CourseSettingsCompilersView.as_view(), name='course_settings_compilers'),
    url(r'^(?P<course_id>[0-9]+)/settings/subgroups/$', views.CourseSettingsSubgroupsView.as_view(), name='course_settings_subgroups'),
]

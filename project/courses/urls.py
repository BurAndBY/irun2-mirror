from django.conf.urls import url

from . import views, settingsviews

urlpatterns = [
    url(r'^$', views.CourseListView.as_view(), name='index'),
    url(r'^new/$', views.CourseCreateView.as_view(), name='new'),

    url(r'^criteria/$', views.CriterionListView.as_view(), name='criterion_index'),
    url(r'^criteria/new/$', views.CriterionCreateView.as_view(), name='criterion_new'),

    url(r'^(?P<course_id>[0-9]+)/$', views.CourseInfoView.as_view(), name='show_course_info'),
    url(r'^(?P<course_id>[0-9]+)/standings/$', views.CourseStandingsView.as_view(), name='course_standings'),
    url(r'^(?P<course_id>[0-9]+)/sheet/$', views.CourseSheetView.as_view(), name='course_sheet'),
    url(r'^(?P<course_id>[0-9]+)/sheet/edit/$', views.CourseSheetEditView.as_view(), name='course_sheet_edit'),
    url(r'^(?P<course_id>[0-9]+)/sheet/edit/api/(?P<membership_id>[0-9]+)/(?P<activity_id>[0-9]+)/$', views.CourseSheetEditApiView.as_view(), name='course_sheet_edit_api'),

    url(r'^(?P<course_id>[0-9]+)/submit/$', views.CourseSubmitView.as_view(), name='course_submit'),

    url(r'^(?P<course_id>[0-9]+)/problemset/$', views.CourseProblemsView.as_view(), name='course_problems'),
    url(r'^(?P<course_id>[0-9]+)/problemset/(?P<topic_id>[0-9]+)/$', views.CourseProblemsTopicView.as_view(), name='course_problems_topic'),
    url(r'^(?P<course_id>[0-9]+)/problemset/(?P<topic_id>[0-9]+)/(?P<problem_id>[0-9]+)/(?P<filename>.+)?$', views.CourseProblemsTopicProblemView.as_view(), name='course_problems_topic_problem'),

    url(r'^(?P<course_id>[0-9]+)/assign/(?P<membership_id>[0-9]+)/$', views.CourseAssignView.as_view(), name='course_assignment'),

    url(r'^(?P<course_id>[0-9]+)/solutions/$', views.CourseAllSolutionsView.as_view(), name='all_solutions'),
    url(r'^(?P<course_id>[0-9]+)/mysolutions/$', views.CourseMySolutionsView.as_view(), name='my_solutions'),

    # Settings

    url(r'^(?P<course_id>[0-9]+)/settings/$', settingsviews.CourseSettingsPropertiesView.as_view(), name='course_settings_properties'),

    url(r'^(?P<course_id>[0-9]+)/settings/delete/$', settingsviews.CourseSettingsDeleteView.as_view(), name='course_settings_delete'),

    url(r'^(?P<course_id>[0-9]+)/settings/topics/$', settingsviews.CourseSettingsTopicsListView.as_view(), name='course_settings_topics'),
    url(r'^(?P<course_id>[0-9]+)/settings/topics/create/$', settingsviews.CourseSettingsTopicsCreateView.as_view(), name='course_settings_topics_create'),
    url(r'^(?P<course_id>[0-9]+)/settings/topics/(?P<pk>[0-9]+)/$', settingsviews.CourseSettingsTopicsUpdateView.as_view(), name='course_settings_topics_update'),

    url(r'^(?P<course_id>[0-9]+)/settings/sheet/$', settingsviews.CourseSettingsSheetActivityListView.as_view(), name='course_settings_sheet'),
    url(r'^(?P<course_id>[0-9]+)/settings/sheet/activities/create/$', settingsviews.CourseSettingsSheetActivityCreateView.as_view(), name='course_settings_sheet_activity_create'),
    url(r'^(?P<course_id>[0-9]+)/settings/sheet/activities/(?P<pk>[0-9]+)/$', settingsviews.CourseSettingsSheetActivityUpdateView.as_view(), name='course_settings_sheet_activity_update'),

    url(r'^(?P<course_id>[0-9]+)/settings/subgroups/$', settingsviews.CourseSettingsSubgroupListView.as_view(), name='course_settings_subgroups'),
    url(r'^(?P<course_id>[0-9]+)/settings/subgroups/new/$', settingsviews.CourseSettingsSubgroupCreateView.as_view(), name='course_settings_subgroup_create'),
    url(r'^(?P<course_id>[0-9]+)/settings/subgroups/(?P<pk>[0-9]+)/$', settingsviews.CourseSettingsSubgroupUpdateView.as_view(), name='course_settings_subgroup_update'),

    url(r'^(?P<course_id>[0-9]+)/settings/users/$', settingsviews.CourseSettingsUsersView.as_view(), name='course_settings_users'),
    url(r'^(?P<course_id>[0-9]+)/settings/users/students/$', settingsviews.CourseSettingsUsersStudentsView.as_view(), name='course_settings_users_students'),
    url(r'^(?P<course_id>[0-9]+)/settings/users/teachers/$', settingsviews.CourseSettingsUsersTeachersView.as_view(), name='course_settings_users_teachers'),
    url(r'^(?P<course_id>[0-9]+)/settings/users/list/(?P<folder_id>[0-9]+)/$', settingsviews.CourseSettingsUsersJsonListView.as_view(), name='course_settings_users_json_list'),

    url(r'^(?P<course_id>[0-9]+)/settings/compilers/$', settingsviews.CourseSettingsCompilersView.as_view(), name='course_settings_compilers'),
    url(r'^(?P<course_id>[0-9]+)/settings/subgroups/$', settingsviews.CourseSettingsSubgroupsView.as_view(), name='course_settings_subgroups'),
]

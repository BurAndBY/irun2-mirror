from django.conf.urls import url

from courses.settings import views as settingsviews


settings_urlpatterns = ([
    url(r'^$', settingsviews.CourseSettingsPropertiesView.as_view(), name='properties'),

    url(r'^delete/$', settingsviews.CourseSettingsDeleteView.as_view(), name='delete'),
    url(r'^clone/$', settingsviews.CourseSettingsCloneView.as_view(), name='clone'),

    url(r'^access/$', settingsviews.CourseSettingsAccessView.as_view(), name='access'),

    url(r'^problems/$', settingsviews.CourseSettingsProblemsView.as_view(), name='problems'),
    url(r'^problems/topics/create/$', settingsviews.CourseSettingsTopicsCreateView.as_view(), name='topics_create'),
    url(r'^problems/topics/(?P<pk>[0-9]+)/$', settingsviews.CourseSettingsTopicsUpdateView.as_view(), name='topics_update'),
    url(r'^problems/topics/(?P<topic_id>[0-9]+)/common/$', settingsviews.CourseSettingsTopicCommonProblemsView.as_view(), name='topic_common_problems'),
    url(r'^problems/common/$', settingsviews.CourseSettingsCommonProblemsView.as_view(), name='common_problems'),
    url(r'^problems/list/(?P<folder_id>[^/]+)/$', settingsviews.CourseSettingsProblemsJsonListView.as_view(), name='problems_json_list'),

    url(r'^sheet/$', settingsviews.CourseSettingsSheetActivityListView.as_view(), name='sheet'),
    url(r'^sheet/activities/create/$', settingsviews.CourseSettingsSheetActivityCreateView.as_view(), name='sheet_activity_create'),
    url(r'^sheet/activities/(?P<pk>[0-9]+)/$', settingsviews.CourseSettingsSheetActivityUpdateView.as_view(), name='sheet_activity_update'),

    url(r'^subgroups/$', settingsviews.CourseSettingsSubgroupListView.as_view(), name='subgroups'),
    url(r'^subgroups/new/$', settingsviews.CourseSettingsSubgroupCreateView.as_view(), name='subgroup_create'),
    url(r'^subgroups/(?P<pk>[0-9]+)/$', settingsviews.CourseSettingsSubgroupUpdateView.as_view(), name='subgroup_update'),

    url(r'^users/$', settingsviews.CourseSettingsUsersView.as_view(), name='users'),
    url(r'^users/students/$', settingsviews.CourseSettingsUsersStudentsView.as_view(), name='users_students'),
    url(r'^users/teachers/$', settingsviews.CourseSettingsUsersTeachersView.as_view(), name='users_teachers'),
    url(r'^users/list/(?P<folder_id>[^/]+)/$', settingsviews.CourseSettingsUsersJsonListView.as_view(), name='users_json_list'),

    url(r'^compilers/$', settingsviews.CourseSettingsCompilersView.as_view(), name='compilers'),

    url(r'^quizzes/$', settingsviews.CourseSettingsQuizzesView.as_view(), name='quizzes'),
    url(r'^quizzes/create/$', settingsviews.CourseSettingsQuizzesCreateView.as_view(), name='quizzes_create'),
    url(r'^quizzes/(?P<instance_id>[0-9]+)/$', settingsviews.CourseSettingsQuizzesUpdateView.as_view(), name='quizzes_update'),

    url(r'^queues/$', settingsviews.CourseSettingsQueuesView.as_view(), name='queues'),
    url(r'^queues/create/$', settingsviews.CourseSettingsQueueCreateView.as_view(), name='queue_create'),
    url(r'^queues/(?P<pk>[0-9]+)/$', settingsviews.CourseSettingsQueueUpdateView.as_view(), name='queue_update'),
], 'settings')

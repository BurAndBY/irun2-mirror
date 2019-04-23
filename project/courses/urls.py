from django.conf.urls import url, include

from courses.settings.urls import settings_urlpatterns
from . import views, globalviews, assignviews, quizviews, queueviews

quiz_urlpatterns = [
    url(r'^$', quizviews.CourseQuizzesView.as_view(), name='list'),
    url(r'^sessions/(?P<session_id>[0-9]+)/$', quizviews.CourseQuizzesSessionView.as_view(), name='session'),
    url(r'^sessions/(?P<session_id>[0-9]+)/answers/$', quizviews.CourseQuizzesAnswersView.as_view(), name='answers'),
    url(r'^sessions/(?P<session_id>[0-9]+)/answers/api/$', quizviews.CourseQuizzesSaveMarkView.as_view(), name='save_mark'),
    url(r'^sessions/(?P<session_id>[0-9]+)/finish/$', quizviews.CourseQuizzesFinishView.as_view(), name='finish'),
    url(r'^sessions/(?P<session_id>[0-9]+)/save-answer/$', quizviews.SaveAnswerAPIView.as_view(), name='save_answer'),
    url(r'^sessions/(?P<session_id>[0-9]+)/delete/$', quizviews.CourseQuizzesDeleteSessionView.as_view(),
        name='delete_session'),
    url(r'^sessions/(?P<session_id>[0-9]+)/submit-comment/$', quizviews.CourseQuizzesSubmitCommentView.as_view(),
        name='submit_comment'),
    url(r'^start/(?P<instance_id>[0-9]+)/$', quizviews.CourseQuizzesStartView.as_view(), name='start'),
    url(r'^rating/(?P<instance_id>[0-9]+)/$', quizviews.CourseQuizzesRatingView.as_view(), name='rating'),
    url(r'^sheet/(?P<instance_id>[0-9]+)/$', quizviews.CourseQuizzesSheetView.as_view(), name='sheet'),
    url(r'^turn-on/(?P<instance_id>[0-9]+)/$', quizviews.CourseQuizzesTurnOnView.as_view(), name='turn_on'),
    url(r'^turn-off/(?P<instance_id>[0-9]+)/$', quizviews.CourseQuizzesTurnOffView.as_view(), name='turn_off'),
]

queue_urlpatterns = [
    url(r'^$', queueviews.ListView.as_view(), name='list'),
    url(r'^(?P<queue_id>[0-9]+)/add/$', queueviews.AddView.as_view(), name='add'),
    url(r'^(?P<queue_id>[0-9]+)/join/$', queueviews.JoinView.as_view(), name='join'),
    url(r'^(?P<queue_id>[0-9]+)/items/(?P<item_id>[0-9]+)/start/$', queueviews.StartView.as_view(), name='start'),
    url(r'^(?P<queue_id>[0-9]+)/items/(?P<item_id>[0-9]+)/finish/$', queueviews.FinishView.as_view(), name='finish'),
]

assignment_urlpatterns = [
    url(r'^$', assignviews.CourseEmptyAssignView.as_view(), name='empty'),
    url(r'^(?P<user_id>[0-9]+)/$', assignviews.CourseAssignView.as_view(), name='index'),
    url(r'^(?P<user_id>[0-9]+)/new-penalty/$', assignviews.CourseAssignCreatePenaltyProblem.as_view(), name='new_penalty'),
    url(r'^(?P<user_id>[0-9]+)/delete-penalty/(?P<assignment_id>[0-9]+)/$',
        assignviews.CourseAssignDeletePenaltyProblem.as_view(), name='delete_penalty'),
    url(r'^(?P<user_id>[0-9]+)/api/problem/$',
        assignviews.CourseAssignProblemApiView.as_view(), name='api_problem'),
    url(r'^(?P<user_id>[0-9]+)/api/criterion/$',
        assignviews.CourseAssignCriterionApiView.as_view(), name='api_criterion'),
    url(r'^(?P<user_id>[0-9]+)/api/topic-problems/(?P<topic_id>[0-9]+)/$',
        assignviews.ListTopicProblemsApiView.as_view()),
]

single_course_urlpatterns = [
    url(r'^$', views.CourseInfoView.as_view(), name='show_course_info'),
    url(r'^standings/$', views.CourseStandingsView.as_view(), name='course_standings'),
    url(r'^standings/wide/$', views.CourseStandingsWideView.as_view(), name='course_standings_wide'),
    url(r'^sheet/$', views.CourseSheetView.as_view(), name='course_sheet'),
    url(r'^sheet/edit/$', views.CourseSheetEditView.as_view(), name='course_sheet_edit'),
    url(r'^sheet/edit/api/(?P<membership_id>[0-9]+)/(?P<activity_id>[0-9]+)/$',
        views.CourseSheetEditApiView.as_view(), name='course_sheet_edit_api'),
    url(r'^compilers/$', views.CourseCompilersView.as_view(), name='course_compilers'),

    url(r'^submit/$', views.CourseSubmitView.as_view(), name='course_submit'),
    url(r'^submission/(?P<solution_id>[0-9]+)/$', views.CourseSubmissionView.as_view(), name='course_submission'),

    url(r'^problemset/$', views.CourseProblemsView.as_view(), name='course_problems'),
    url(r'^problemset/(?P<topic_id>[0-9]+)/$', views.CourseProblemsTopicView.as_view(), name='course_problems_topic'),
    url(r'^problemset/(?P<topic_id>[0-9]+)/(?P<problem_id>[0-9]+)/(?P<filename>.+)?$',
        views.CourseProblemsTopicProblemView.as_view(), name='course_problems_topic_problem'),
    url(r'^problems/(?P<problem_id>[0-9]+)/(?P<filename>.+)?$',
        views.CourseProblemsProblemView.as_view(), name='course_problems_problem'),

    url(r'^solutions/$', views.CourseAllSolutionsView.as_view(), name='all_solutions'),
    url(r'^my/solutions/$', views.CourseMySolutionsView.as_view(), name='my_solutions'),

    url(r'^my/problems/$', views.CourseMyProblemsView.as_view(), name='my_problems'),

    url(r'^my/attempts/$', views.CourseMyAttemptsView.as_view(), name='my_attempts'),

    # Messages

    url(r'^mailbox/$', views.CourseMessagesEmptyView.as_view(), name='messages_empty'),
    url(r'^mailbox/(?P<thread_id>[0-9]+)/$', views.CourseMessagesView.as_view(), name='messages'),
    url(r'^mailbox/(?P<thread_id>[0-9]+)/delete/$', views.CourseMessagesThreadDeleteView.as_view(), name='messages_thread_delete'),
    url(r'^mailbox/(?P<thread_id>[0-9]+)/resolve/$', views.CourseMessagesThreadResolveView.as_view(), name='messages_thread_resolve'),
    url(r'^mailbox/(?P<thread_id>[0-9]+)/messages/(?P<message_id>[0-9]+)/attachment/(?P<filename>.*)$',
        views.CourseMessagesDownloadView.as_view(), name='messages_download'),
    url(r'^mailbox/new/$', views.CourseMessagesNewView.as_view(), name='messages_new'),

    url(r'^quizzes/', include(quiz_urlpatterns, namespace='quizzes')),
    url(r'^queues/', include(queue_urlpatterns, namespace='queues')),
    url(r'^settings/', include(settings_urlpatterns, namespace='settings')),
    url(r'^assign/', include(assignment_urlpatterns, namespace='assignment')),
]

urlpatterns = [
    url(r'^$', globalviews.ActiveCourseListView.as_view(), name='index'),
    url(r'^all/$', globalviews.AllCourseListView.as_view(), name='index_all'),
    url(r'^my/$', globalviews.MyCourseListView.as_view(), name='my'),
    url(r'^new/$', globalviews.CourseCreateView.as_view(), name='new'),

    url(r'^criteria/$', views.CriterionListView.as_view(), name='criterion_index'),
    url(r'^criteria/new/$', views.CriterionCreateView.as_view(), name='criterion_new'),
    url(r'^criteria/(?P<pk>[0-9]+)/edit/$', views.CriterionUpdateView.as_view(), name='criterion_edit'),
    url(r'^criteria/(?P<pk>[0-9]+)/delete/$', views.CriterionDeleteView.as_view(), name='criterion_delete'),

    url(r'^(?P<course_id>[0-9]+)/', include(single_course_urlpatterns)),
]

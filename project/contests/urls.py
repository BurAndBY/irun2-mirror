from django.conf.urls import include, url

from . import views, globalviews, settingsviews

contest_urlpatterns = [
    url(r'^$', views.GeneralView.as_view()),
    url(r'^standings/$', views.StandingsView.as_view(), name='standings'),
    url(r'^standings/wide/$', views.StandingsView.as_view(wide=True), name='standings_wide'),
    url(r'^standings/raw/$', views.StandingsView.as_view(raw=True), name='standings_raw'),
    url(r'^statements/(?P<filename>.+)$', views.StatementsFileView.as_view(), name='statements'),
    url(r'^problems/$', views.ProblemsView.as_view(), name='problems'),
    url(r'^problems/(?P<problem_id>[0-9]+)/(?P<filename>.+)?$', views.ProblemView.as_view(), name='problem'),
    url(r'^solutions/$', views.AllSolutionsView.as_view(), name='all_solutions'),
    url(r'^my/solutions/$', views.MySolutionsView.as_view(), name='my_solutions'),
    url(r'^submit/$', views.SubmitView.as_view(), name='submit'),
    url(r'^submission/(?P<solution_id>[0-9]+)/$', views.SubmissionView.as_view(), name='submission'),
    url(r'^messages/$', views.MessagesView.as_view(), name='messages'),
    url(r'^messages/new/$', views.NewMessageView.as_view(), name='messages_new'),
    url(r'^messages/(?P<message_id>[0-9]+)/edit/$', views.EditMessageView.as_view(), name='messages_edit'),
    url(r'^messages/(?P<message_id>[0-9]+)/delete/$', views.DeleteMessageView.as_view(), name='messages_delete'),
    url(r'^questions/$', views.AllQuestionsView.as_view(), name='all_questions'),
    url(r'^questions/(?P<message_id>[0-9]+)/$', views.AllQuestionsAnswersView.as_view(), name='all_questions_answers'),
    url(r'^questions/(?P<message_id>[0-9]+)/delete/$', views.AllQuestionsDeleteView.as_view(), name='all_questions_delete'),
    url(r'^my/questions/$', views.MyQuestionsView.as_view(), name='my_questions'),
    url(r'^my/questions/(?P<message_id>[0-9]+)/$', views.MyQuestionsAnswersView.as_view(), name='my_questions_answers'),
    url(r'^my/questions/new/$', views.MyQuestionsNewView.as_view(), name='my_questions_new'),
    url(r'^compilers/$', views.CompilersView.as_view(), name='compilers'),
]

contestsettings_urlpatterns = [
    url(r'^$', settingsviews.PropertiesView.as_view(), name='settings_properties'),
    url(r'^delete/$', settingsviews.DeleteView.as_view(), name='settings_delete'),
    url(r'^compilers/$', settingsviews.CompilersView.as_view(), name='settings_compilers'),
    url(r'^problems/$', settingsviews.ProblemsView.as_view(), name='settings_problems'),
    url(r'^statements/$', settingsviews.StatementsView.as_view(), name='settings_statements'),
    url(r'^problems/list/(?P<folder_id>[0-9]+)/$', settingsviews.ProblemsJsonListView.as_view(), name='settings_problems_json_list'),
    url(r'^users/$', settingsviews.UsersView.as_view(), name='settings_users'),
    url(r'^users/(?P<tag>[a-z]+)/$', settingsviews.UserRoleView.as_view(), name='settings_user_role'),
    url(r'^users/list/(?P<folder_id>[0-9]+)/$', settingsviews.UsersJsonListView.as_view(), name='settings_users_json_list'),
]

urlpatterns = [
    url(r'^$', globalviews.ContestListView.as_view(), name='index'),
    url(r'^new/$', globalviews.ContestCreateView.as_view(), name='new'),

    url(r'^(?P<contest_id>[0-9]+)/', include(contest_urlpatterns)),
    url(r'^(?P<contest_id>[0-9]+)/settings/', include(contestsettings_urlpatterns)),
]

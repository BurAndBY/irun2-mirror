from django.conf.urls import include, url

from . import views, globalviews, settingsviews

app_name = 'contests'

contest_urlpatterns = [
    url(r'^$', views.GeneralView.as_view()),
    url(r'^standings/$', views.StandingsView.as_view(), name='standings'),
    url(r'^standings/wide/$', views.StandingsView.as_view(wide=True), name='standings_wide'),
    url(r'^standings/raw/$', views.StandingsView.as_view(raw=True), name='standings_raw'),
    url(r'^statements/(?P<filename>.+)$', views.StatementsFileView.as_view(), name='statements'),
    url(r'^problems/$', views.ProblemsView.as_view(), name='problems'),
    url(r'^problems/(?P<problem_id>[0-9]+)/$', views.ProblemView.as_view(), name='problem'),
    url(r'^problems/(?P<problem_id>[0-9]+)/(?P<filename>.+)$', views.ProblemFileView.as_view(), name='problem_file'),
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
    url(r'^export/$', views.ExportView.as_view(), name='export'),
    url(r'^export/S4RiS-StanD\.json$', views.S4RiSExportView.as_view(), name='export_s4ris'),
    url(r'^export/ejudge\.xml$', views.EjudgeExportView.as_view(), name='export_ejudge'),
    url(r'^printing/$', views.PrintingView.as_view(), name='printing'),
    url(r'^printouts/new/$', views.NewPrintoutView.as_view(), name='new_printout'),
    url(r'^printouts/(?P<printout_id>[0-9]+)/$', views.ShowPrintoutView.as_view(), name='show_printout'),
    url(r'^printouts/(?P<printout_id>[0-9]+)/edit/$', views.EditPrintoutView.as_view(), name='edit_printout'),
]

contestsettings_urlpatterns = [
    url(r'^$', settingsviews.PropertiesView.as_view(), name='settings_properties'),
    url(r'^access/$', settingsviews.AccessView.as_view(), name='settings_access'),
    url(r'^limits/$', settingsviews.LimitsView.as_view(), name='settings_limits'),
    url(r'^delete/$', settingsviews.DeleteView.as_view(), name='settings_delete'),
    url(r'^compilers/$', settingsviews.CompilersView.as_view(), name='settings_compilers'),
    url(r'^problems/$', settingsviews.ProblemsView.as_view(), name='settings_problems'),
    url(r'^statements/$', settingsviews.StatementsView.as_view(), name='settings_statements'),
    url(r'^problems/list/(?P<folder_id>[^/]+)/$', settingsviews.ProblemsJsonListView.as_view(), name='settings_problems_json_list'),
    url(r'^users/$', settingsviews.UsersView.as_view(), name='settings_users'),
    url(r'^users/(?P<tag>[a-z]+)/$', settingsviews.UserRoleView.as_view(), name='settings_user_role'),
    url(r'^users/list/(?P<folder_id>[^/]+)/$', settingsviews.UsersJsonListView.as_view(), name='settings_users_json_list'),
    url(r'^filters/$', settingsviews.UsersFilterVew.as_view(), name='settings_filters'),
    url(r'^printing/$', settingsviews.PrintingView.as_view(), name='settings_printing'),
]

urlpatterns = [
    url(r'^$', globalviews.ContestListView.as_view(), name='index'),
    url(r'^my/$', globalviews.MyContestListView.as_view(), name='my'),
    url(r'^new/$', globalviews.ContestCreateView.as_view(), name='new'),

    url(r'^(?P<contest_id>[0-9]+)/', include(contest_urlpatterns)),
    url(r'^(?P<contest_id>[0-9]+)/settings/', include(contestsettings_urlpatterns)),
]

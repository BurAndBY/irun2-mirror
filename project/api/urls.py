from django.conf.urls import url

from . import views
from contests.globalviews import ContestsApiView

app_name = 'api'

urlpatterns = [
    # ex: /polls/
    url(r'^fs/status$', views.FileStatusView.as_view(), name='fs_status'),
    url(r'^fs/(?P<filename>[0-9a-f]*)$', views.FileView.as_view()),
    url(r'^fs/(?P<filename>new)$', views.NewFileView.as_view()),
    url(r'^jobs/take$', views.JobTakeView.as_view(), name='take_job'),
    url(r'^jobs/(?P<job_id>\d+)/result$', views.JobPutResultView.as_view()),
    url(r'^jobs/(?P<job_id>\d+)/state$', views.JobPutStateView.as_view()),
    url(r'^jobs/(?P<job_id>\d+)/cancel$', views.JobCancelView.as_view()),
    url(r'^compiler-settings$', views.CompilerSettingsView.as_view()),
    url(r'^plagiarism/take$', views.PlagiarismTakeView.as_view()),
    url(r'^plagiarism/put$', views.PlagiarismPutView.as_view()),
    url(r'^sleep$', views.SleepView.as_view()),
    url(r'^printing$', views.PrintingView.as_view()),
    url(r'^printing/(?P<printout_id>\d+)$', views.PrintingDoneView.as_view()),
    url(r'^auth/check$', views.AuthCheckView.as_view()),
    url(r'^contests$', ContestsApiView.as_view()),

    url(r'^queue/$', views.QueueView.as_view(), name='queue')
]

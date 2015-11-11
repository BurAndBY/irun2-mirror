from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /polls/
    url(r'^fs/status$', views.FileStatusView.as_view(), name='fs_status'),
    url(r'^fs/(?P<filename>[0-9a-f]*)$', views.FileView.as_view(), name='fs_status'),
    url(r'^jobs/take$', views.JobTakeView.as_view(), name='take_job'),
    url(r'^jobs/(?P<job_id>\d+)/result$', views.JobPutResult.as_view()),
]

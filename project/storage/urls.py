from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^new/$', views.NewView.as_view(), name='new'),
    url(r'^stats/$', views.StatisticsView.as_view(), name='statistics'),
    url(r'^resource/(?P<resource_id>[0-9a-f]*)/$', views.ShowView.as_view(), name='show'),
    url(r'^resource/(?P<resource_id>[0-9a-f]*)/download/$', views.DownloadView.as_view(), name='download'),
]

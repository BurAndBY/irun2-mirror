from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^new/$', views.CreateRejudgeView.as_view(), name='create_rejudge'),
    url(r'^(?P<rejudge_id>[0-9]+)/$', views.RejudgeView.as_view(), name='rejudge'),
    url(r'^(?P<rejudge_id>[0-9]+)/status/json/$', views.RejudgeJsonView.as_view(), name='rejudge_status_json'),
    url(r'^$', views.RejudgeListView.as_view(), name='rejudge_list'),
]

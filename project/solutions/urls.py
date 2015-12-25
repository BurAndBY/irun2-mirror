from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^judgements/(?P<judgement_id>[0-9]+)/$', views.show_judgement, name='show_judgement'),
    url(r'^ad-hoc/$', views.AdHocView.as_view(), name='ad_hoc'),
    url(r'^rejudge/$', views.CreateRejudgeView.as_view(), name='create_rejudge'),
    url(r'^rejudges/(?P<rejudge_id>[0-9]+)/$', views.RejudgeView.as_view(), name='rejudge'),
    url(r'^full/$', views.SolutionListView.as_view(), name='list'),
    url(r'^$', views.ilist),
    #url(r'^table/data/$', views.MyDataView.as_view(), name='table_data'),
]

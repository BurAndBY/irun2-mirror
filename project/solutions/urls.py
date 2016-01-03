from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^judgements/(?P<judgement_id>[0-9]+)/$', views.show_judgement, name='show_judgement'),
    url(r'^ad-hoc/$', views.AdHocView.as_view(), name='ad_hoc'),
    url(r'^rejudge/$', views.CreateRejudgeView.as_view(), name='create_rejudge'),
    url(r'^rejudges/(?P<rejudge_id>[0-9]+)/$', views.RejudgeView.as_view(), name='rejudge'),
    url(r'^full/$', views.SolutionListView.as_view(), name='list'),
    url(r'^$', views.ilist),

    url(r'^(?P<solution_id>[0-9]+)/$', views.SolutionMainView.as_view(), name='main'),
    url(r'^(?P<solution_id>[0-9]+)/source/$', views.SolutionSourceView.as_view(), name='source'),
    url(r'^(?P<solution_id>[0-9]+)/log/$', views.SolutionLogView.as_view(), name='log'),
    url(r'^(?P<solution_id>[0-9]+)/tests/$', views.SolutionTestsView.as_view(), name='tests'),

    url(r'^(?P<solution_id>[0-9]+)/tests/(?P<testcaseresult_id>[0-9]+)/$', views.SolutionTestCaseResultView.as_view(), name='test_case_result'),
    url(r'^(?P<solution_id>[0-9]+)/tests/(?P<testcaseresult_id>[0-9]+)/(?P<mode>input|output|answer|stdout|stderr)\.txt$', views.SolutionTestCaseResultDataView.as_view(), name='test_data'),
    #url(r'^table/data/$', views.MyDataView.as_view(), name='table_data'),

    url(r'^(?P<solution_id>[0-9]+)/source/open/(?P<filename>.*)$', views.SolutionSourceOpenView.as_view(), name='source_open'),
    url(r'^(?P<solution_id>[0-9]+)/source/download/(?P<filename>.*)$', views.SolutionSourceDownloadView.as_view(), name='source_download'),
]

from django.conf.urls import include, url

from . import views

solutions_urlpatterns = [
    url(r'^$', views.SolutionListView.as_view(), name='list'),

    url(r'^(?P<solution_id>[0-9]+)/$', views.SolutionMainView.as_view(), name='main'),
    url(r'^(?P<solution_id>[0-9]+)/source/$', views.SolutionSourceView.as_view(), name='source'),
    url(r'^(?P<solution_id>[0-9]+)/log/$', views.SolutionLogView.as_view(), name='log'),
    url(r'^(?P<solution_id>[0-9]+)/tests/$', views.SolutionTestsView.as_view(), name='tests'),
    url(r'^(?P<solution_id>[0-9]+)/runs/$', views.SolutionJudgementsView.as_view(), name='judgements'),
    url(r'^(?P<solution_id>[0-9]+)/attempts/$', views.SolutionAttemptsView.as_view(), name='attempts'),
    url(r'^(?P<solution_id>[0-9]+)/plagiarism/$', views.SolutionPlagiarismView.as_view(), name='plagiarism'),
    url(r'^(?P<solution_id>[0-9]+)/status/json/$', views.SolutionStatusJsonView.as_view(), name='status_json'),

    url(r'^(?P<solution_id>[0-9]+)/tests/(?P<testcaseresult_id>[0-9]+)/$', views.SolutionTestCaseResultView.as_view(), name='test_case_result'),
    url(r'^(?P<solution_id>[0-9]+)/tests/(?P<testcaseresult_id>[0-9]+)/(?P<mode>input|output|answer|stdout|stderr)\.txt$', views.SolutionTestCaseResultDataView.as_view(), name='test_data'),
    url(r'^(?P<solution_id>[0-9]+)/tests/(?P<testcaseresult_id>[0-9]+)/images/(?P<filename>.*)$', views.SolutionTestCaseResultImageView.as_view(), name='test_image'),

    url(r'^(?P<solution_id>[0-9]+)/source/open/(?P<filename>.*)$', views.SolutionSourceOpenView.as_view(), name='source_open'),
    url(r'^(?P<solution_id>[0-9]+)/source/download/(?P<filename>.*)$', views.SolutionSourceDownloadView.as_view(), name='source_download'),

    url(r'^delete/$', views.DeleteSolutionsView.as_view(), name='delete'),

    url(r'^compare/$', views.CompareSolutionsView.as_view(), name='compare'),
]

judgements_urlpatterns = [
    url(r'^$', views.JudgementListView.as_view(), name='judgement_list'),
    url(r'^(?P<judgement_id>[0-9]+)/$', views.JudgementView.as_view(), name='show_judgement'),
    url(r'^(?P<judgement_id>[0-9]+)/tests/(?P<testcaseresult_id>[0-9]+)/$', views.JudgementTestCaseResultView.as_view(), name='judgement_testcaseresult'),
    url(r'^(?P<judgement_id>[0-9]+)/tests/(?P<testcaseresult_id>[0-9]+)/(?P<mode>input|output|answer|stdout|stderr)\.txt$', views.JudgementTestCaseResultDataView.as_view(), name='judgement_testdata'),
    url(r'^(?P<judgement_id>[0-9]+)/tests/(?P<testcaseresult_id>[0-9]+)/images/(?P<filename>.*)$', views.JudgementTestCaseResultImageView.as_view(), name='judgement_testimage'),
]

rejudges_urlpatterns = [
    url(r'^new/$', views.CreateRejudgeView.as_view(), name='create_rejudge'),
    url(r'^(?P<rejudge_id>[0-9]+)/$', views.RejudgeView.as_view(), name='rejudge'),
    url(r'^(?P<rejudge_id>[0-9]+)/status/json/$', views.RejudgeJsonView.as_view(), name='rejudge_status_json'),
    url(r'^$', views.RejudgeListView.as_view(), name='rejudge_list'),
]

urlpatterns = [
    url(r'^solutions/', include(solutions_urlpatterns)),
    url(r'^runs/', include(judgements_urlpatterns)),
    url(r'^rejudges/', include(rejudges_urlpatterns)),
]

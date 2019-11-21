from django.conf.urls import include, url

from . import views

single_judgement_urlpatterns = [
    url(r'^$', views.JudgementView.as_view(), name='show_judgement'),
    url(r'^storage/$', views.JudgementStorageView.as_view(), name='show_judgement_storage'),
    url(r'^tests/(?P<testcaseresult_id>[0-9]+)/$', views.JudgementTestCaseResultView.as_view(), name='judgement_testcaseresult'),
    url(r'^tests/(?P<testcaseresult_id>[0-9]+)/(?P<mode>input|output|answer|stdout|stderr)\.txt$', views.JudgementTestCaseResultDataView.as_view(), name='judgement_testdata'),
    url(r'^tests/(?P<testcaseresult_id>[0-9]+)/images/(?P<filename>.*)$', views.JudgementTestCaseResultImageView.as_view(), name='judgement_testimage'),
]

urlpatterns = [
    url(r'^(?P<judgement_id>[0-9]+)/', include(single_judgement_urlpatterns))
]

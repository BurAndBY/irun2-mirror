from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^new/$', views.ProblemFormNewView.as_view(), name='new'),
    url(r'^(?P<problem_id>[0-9]+)/$', views.overview, name='overview'),
    url(r'^(?P<problem_id>[0-9]+)/statement/$', views.statement, name='statement'),
    url(r'^(?P<problem_id>[0-9]+)/statement/(?P<filename>.+)$', views.statement_file, name='statement_file'),
    url(r'^(?P<problem_id>[0-9]+)/edit/$', views.ProblemFormEditView.as_view(), name='edit'),
    url(r'^(?P<problem_id>[0-9]+)/tests/$', views.tests, name='tests'),
    url(r'^(?P<problem_id>[0-9]+)/tests/add/$', views.add_test, name='add_test'),
    url(r'^(?P<problem_id>[0-9]+)/tests/(?P<test_number>[0-9]+)/$', views.show_test, name='show_test'),
]

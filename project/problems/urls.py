from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^tree/$', views.show_tree, name='show_tree'),
    url(r'^tree/(?P<folder_id>[0-9]+)/$', views.show_folder, name='show_folder'),
    url(r'^tree/(?P<folder_id>[0-9]+)/json/$', views.show_folder_json, name='show_folder_json'),
    url(r'^new/$', views.ProblemFormNewView.as_view(), name='new'),
    url(r'^(?P<problem_id>[0-9]+)/$', views.overview, name='overview'),
    url(r'^(?P<problem_id>[0-9]+)/statement/(?P<filename>.+)?$', views.ProblemStatementView.as_view(), name='statement'),
    url(r'^(?P<problem_id>[0-9]+)/edit/$', views.ProblemFormEditView.as_view(), name='edit'),
    url(r'^(?P<problem_id>[0-9]+)/tests/$', views.tests, name='tests'),
    url(r'^(?P<problem_id>[0-9]+)/tests/add/$', views.add_test, name='add_test'),
    url(r'^(?P<problem_id>[0-9]+)/tests/(?P<test_number>[0-9]+)/$', views.show_test, name='show_test'),
]

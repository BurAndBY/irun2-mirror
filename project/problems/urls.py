from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^tree/$', views.ShowTreeView.as_view(), name='show_tree'),
    url(r'^tree/(?P<folder_id>[0-9]+)/$', views.ShowTreeFolderView.as_view(), name='show_tree_folder'),
    url(r'^tree/(?P<folder_id>[0-9]+)/json/$', views.ShowTreeFolderJsonView.as_view(), name='show_tree_folder_json'),

    url(r'^(?P<problem_id>[0-9]+)/$', views.ProblemOverviewView.as_view(), name='overview'),
    url(r'^(?P<problem_id>[0-9]+)/statement/(?P<filename>.+)?$', views.ProblemStatementView.as_view(), name='statement'),
    url(r'^(?P<problem_id>[0-9]+)/edit/$', views.ProblemEditView.as_view(), name='edit'),
    url(r'^(?P<problem_id>[0-9]+)/tests/$', views.ProblemTestsView.as_view(), name='tests'),
    #url(r'^(?P<problem_id>[0-9]+)/tests/add/$', views.add_test, name='add_test'),
    url(r'^(?P<problem_id>[0-9]+)/tests/(?P<test_number>[0-9]+)/$', views.ProblemTestsTestView.as_view(), name='show_test'),
    url(r'^(?P<problem_id>[0-9]+)/solutions/$', views.ProblemSolutionsView.as_view(), name='solutions'),
    url(r'^(?P<problem_id>[0-9]+)/files/$', views.ProblemFilesView.as_view(), name='files'),
    url(r'^(?P<problem_id>[0-9]+)/files/(?P<file_id>[0-9]+)/(?P<filename>.*)$', views.ProblemFilesFileOpenView.as_view(), name='file_open'),
    url(r'^(?P<problem_id>[0-9]+)/submit/$', views.ProblemSubmitView.as_view(), name='submit'),
    url(r'^(?P<problem_id>[0-9]+)/submission/(?P<solution_id>[0-9]+)/$', views.ProblemSubmissionView.as_view(), name='submission'),

    url(r'^folders/(?P<folder_id_or_root>[0-9]+|root)/$', views.ShowFolderView.as_view(), name='show_folder'),
    url(r'^search/$', views.SearchView.as_view(), name='search'),
]

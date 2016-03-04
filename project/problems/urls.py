from django.conf.urls import include, url

from . import views

problem_urlpatterns = [
    url(r'^$', views.ProblemOverviewView.as_view(), name='overview'),
    url(r'^statement/(?P<filename>.+)?$', views.ProblemStatementView.as_view(), name='statement'),
    url(r'^edit/$', views.ProblemEditView.as_view(), name='edit'),

    url(r'^tests/$', views.ProblemTestsView.as_view(), name='tests'),
    url(r'^tests/(?P<test_number>[0-9]+)/$', views.ProblemTestsTestView.as_view(), name='show_test'),
    url(r'^tests/(?P<test_number>[0-9]+)/edit/$', views.ProblemTestsTestEditView.as_view(), name='edit_test'),
    url(r'^tests/(?P<test_number>[0-9]+)/image/(?P<filename>.*)$', views.ProblemTestsTestImageView.as_view(), name='test_image'),

    url(r'^solutions/$', views.ProblemSolutionsView.as_view(), name='solutions'),

    url(r'^files/$', views.ProblemFilesView.as_view(), name='files'),
    url(r'^files/data/(?P<file_id>[0-9]+)/get/(?P<filename>.*)$', views.ProblemFilesFileOpenView.as_view(), name='data_file_open'),
    url(r'^files/data/(?P<file_id>[0-9]+)/edit/$', views.ProblemFilesDataFileEditView.as_view(), name='data_file_edit'),
    url(r'^files/source/(?P<file_id>[0-9]+)/get/(?P<filename>.*)$', views.ProblemFilesSourceFileOpenView.as_view(), name='source_file_open'),
    url(r'^files/source/(?P<file_id>[0-9]+)/edit/$', views.ProblemFilesSourceFileEditView.as_view(), name='source_file_edit'),

    url(r'^submit/$', views.ProblemSubmitView.as_view(), name='submit'),
    url(r'^submission/(?P<solution_id>[0-9]+)/$', views.ProblemSubmissionView.as_view(), name='submission'),
]

urlpatterns = [
    url(r'^tree/$', views.ShowTreeView.as_view(), name='show_tree'),
    url(r'^tree/(?P<folder_id>[0-9]+)/$', views.ShowTreeFolderView.as_view(), name='show_tree_folder'),
    url(r'^tree/(?P<folder_id>[0-9]+)/json/$', views.ShowTreeFolderJsonView.as_view(), name='show_tree_folder_json'),

    url(r'^(?P<problem_id>[0-9]+)/', include(problem_urlpatterns)),

    url(r'^folders/(?P<folder_id_or_root>[0-9]+|root)/$', views.ShowFolderView.as_view(), name='show_folder'),
    url(r'^search/$', views.SearchView.as_view(), name='search'),

    url(r'^tex/$', views.TeXView.as_view(), name='tex'),
    url(r'^tex/render/$', views.TeXRenderView.as_view(), name='tex_render'),
]

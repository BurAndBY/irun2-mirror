from django.conf.urls import include, url

from . import views

problem_urlpatterns = [
    url(r'^$', views.ProblemOverviewView.as_view(), name='overview'),
    url(r'^statement/(?P<filename>.+)?$', views.ProblemStatementView.as_view(), name='statement'),

    url(r'^tests/$', views.ProblemTestsView.as_view(), name='tests'),
    url(r'^tests/(?P<test_number>[0-9]+)/$', views.ProblemTestsTestView.as_view(), name='show_test'),
    url(r'^tests/upload/$', views.ProblemTestsUploadArchiveView.as_view(), name='upload_archive'),
    url(r'^tests/new/$', views.ProblemTestsNewView.as_view(), name='new_test'),
    url(r'^tests/(?P<test_number>[0-9]+)/edit/$', views.ProblemTestsTestEditView.as_view(), name='edit_test'),
    url(r'^tests/(?P<test_number>[0-9]+)/delete/$', views.ProblemTestsDeleteView.as_view(), name='delete_test'),
    url(r'^tests/(?P<test_number>[0-9]+)/image/(?P<filename>.+)$', views.ProblemTestsTestImageView.as_view(), name='test_image'),
    url(r'^tests/batch/set/time-limit/$', views.ProblemTestsSetTimeLimitView.as_view(), name='tests_mass_time_limit'),
    url(r'^tests/batch/set/memory-limit/$', views.ProblemTestsSetMemoryLimitView.as_view(), name='tests_mass_memory_limit'),

    url(r'^tests/open/input-(?P<test_number>[0-9]+)\.txt$', views.ProblemTestsTestDataView.as_view(kind='input', download=False), name='test_input_open'),
    url(r'^tests/download/input-(?P<test_number>[0-9]+)\.txt$', views.ProblemTestsTestDataView.as_view(kind='input', download=True), name='test_input_download'),
    url(r'^tests/open/answer-(?P<test_number>[0-9]+)\.txt$', views.ProblemTestsTestDataView.as_view(kind='answer', download=False), name='test_answer_open'),
    url(r'^tests/download/answer-(?P<test_number>[0-9]+)\.txt$', views.ProblemTestsTestDataView.as_view(kind='answer', download=True), name='test_answer_download'),

    url(r'^solutions/$', views.ProblemSolutionsView.as_view(), name='solutions'),

    url(r'^files/$', views.ProblemFilesView.as_view(), name='files'),
    url(r'^files/data/(?P<file_id>[0-9]+)/open/(?P<filename>.+)$', views.ProblemFilesFileOpenView.as_view(), name='data_file_open'),
    url(r'^files/data/(?P<file_id>[0-9]+)/download/(?P<filename>.+)$', views.ProblemFilesFileOpenView.as_view(download=True), name='data_file_download'),
    url(r'^files/data/(?P<file_id>[0-9]+)/edit/$', views.ProblemFilesDataFileEditView.as_view(), name='data_file_edit'),
    url(r'^files/data/(?P<file_id>[0-9]+)/delete/$', views.ProblemFilesDataFileDeleteView.as_view(), name='data_file_delete'),
    url(r'^files/data/new/$', views.ProblemFilesDataFileNewView.as_view(), name='data_file_new'),

    url(r'^files/source/(?P<file_id>[0-9]+)/open/(?P<filename>.+)$', views.ProblemFilesSourceFileOpenView.as_view(), name='source_file_open'),
    url(r'^files/source/(?P<file_id>[0-9]+)/download/(?P<filename>.+)$', views.ProblemFilesSourceFileOpenView.as_view(download=True), name='source_file_download'),
    url(r'^files/source/(?P<file_id>[0-9]+)/edit/$', views.ProblemFilesSourceFileEditView.as_view(), name='source_file_edit'),
    url(r'^files/source/(?P<file_id>[0-9]+)/delete/$', views.ProblemFilesSourceFileDeleteView.as_view(), name='source_file_delete'),
    url(r'^files/source/new/$', views.ProblemFilesSourceFileNewView.as_view(), name='source_file_new'),

    url(r'^tex/$', views.ProblemTeXView.as_view(), name='tex'),
    url(r'^tex/render/$', views.ProblemTeXRenderView.as_view(), name='tex_render'),
    url(r'^tex/new/statement/$', views.ProblemTeXNewStatementView.as_view(), name='tex_new_statement'),
    url(r'^tex/(?P<file_id>[0-9]+)/$', views.ProblemTeXEditView.as_view(), name='edit_tex'),
    url(r'^tex/(?P<file_id>[0-9]+)/(?P<filename>.+)$', views.ProblemTeXEditRelatedFileView.as_view()),

    url(r'^submit/$', views.ProblemSubmitView.as_view(), name='submit'),
    url(r'^submission/(?P<solution_id>[0-9]+)/$', views.ProblemSubmissionView.as_view(), name='submission'),
    url(r'^folders/$', views.ProblemFoldersView.as_view(), name='folders'),
    url(r'^properties/$', views.ProblemPropertiesView.as_view(), name='properties'),
    url(r'^pictures/$', views.ProblemPicturesView.as_view(), name='pictures'),
    url(r'^validator/$', views.ProblemValidatorView.as_view(), name='validator'),
]

urlpatterns = [
    url(r'^tree/$', views.ShowTreeView.as_view(), name='show_tree'),
    url(r'^tree/(?P<folder_id>[0-9]+)/$', views.ShowTreeFolderView.as_view(), name='show_tree_folder'),
    url(r'^tree/(?P<folder_id>[0-9]+)/json/$', views.ShowTreeFolderJsonView.as_view(), name='show_tree_folder_json'),

    url(r'^(?P<problem_id>[0-9]+)/', include(problem_urlpatterns)),

    url(r'^folders/(?P<folder_id_or_root>[0-9]+|root)/$', views.ShowFolderView.as_view(), name='show_folder'),
    url(r'^search/$', views.SearchView.as_view(), name='search'),

    url(r'^tex/$', views.TeXView.as_view(), name='tex_playground'),
    url(r'^tex/render/$', views.TeXRenderView.as_view(), name='tex_playground_render'),
]

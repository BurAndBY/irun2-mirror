from django.conf.urls import include, url

from problems.problem import views as pviews

problem_urlpatterns = [
    url(r'^$', pviews.ProblemOverviewView.as_view(), name='overview'),
    url(r'^statement/(?P<filename>.+)?$', pviews.ProblemStatementView.as_view(), name='statement'),

    url(r'^tests/$', pviews.ProblemTestsView.as_view(), name='tests'),
    url(r'^tests/browse/$', pviews.ProblemBrowseTestsView.as_view(), name='browse_tests'),
    url(r'^tests/reorder/$', pviews.ProblemReorderTestsView.as_view(), name='reorder_tests'),
    url(r'^tests/(?P<test_number>[0-9]+)/$', pviews.ProblemTestsTestView.as_view(), name='show_test'),
    url(r'^tests/upload/$', pviews.ProblemTestsUploadArchiveView.as_view(), name='upload_archive'),
    url(r'^tests/new/$', pviews.ProblemTestsNewView.as_view(), name='new_test'),
    url(r'^tests/(?P<test_number>[0-9]+)/edit/$', pviews.ProblemTestsTestEditView.as_view(), name='edit_test'),
    url(r'^tests/(?P<test_number>[0-9]+)/delete/$', pviews.ProblemTestsDeleteView.as_view(), name='delete_test'),
    url(r'^tests/(?P<test_number>[0-9]+)/image/(?P<filename>.+)$', pviews.ProblemTestsTestImageView.as_view(), name='test_image'),
    url(r'^tests/batch/set/time-limit/$', pviews.ProblemTestsSetTimeLimitView.as_view(), name='tests_mass_time_limit'),
    url(r'^tests/batch/set/memory-limit/$', pviews.ProblemTestsSetMemoryLimitView.as_view(), name='tests_mass_memory_limit'),
    url(r'^tests/batch/set/points/$', pviews.ProblemTestsSetPointsView.as_view(), name='tests_mass_points'),
    url(r'^tests/batch/delete/$', pviews.ProblemTestsBatchDeleteView.as_view(), name='tests_mass_delete'),
    url(r'^tests/batch/download/$', pviews.ProblemTestsDownloadArchiveView.as_view(), name='tests_batch_download'),

    url(r'^tests/open/input-(?P<test_number>[0-9]+)\.txt$', pviews.ProblemTestsTestDataView.as_view(kind='input', download=False), name='test_input_open'),
    url(r'^tests/download/input-(?P<test_number>[0-9]+)\.txt$', pviews.ProblemTestsTestDataView.as_view(kind='input', download=True), name='test_input_download'),
    url(r'^tests/open/answer-(?P<test_number>[0-9]+)\.txt$', pviews.ProblemTestsTestDataView.as_view(kind='answer', download=False), name='test_answer_open'),
    url(r'^tests/download/answer-(?P<test_number>[0-9]+)\.txt$', pviews.ProblemTestsTestDataView.as_view(kind='answer', download=True), name='test_answer_download'),

    url(r'^solutions/$', pviews.ProblemSolutionsView.as_view(), name='solutions'),
    url(r'^solutions/process/$', pviews.ProblemSolutionsProcessView.as_view(), name='solutions_process'),

    url(r'^files/$', pviews.ProblemFilesView.as_view(), name='files'),
    url(r'^files/data/(?P<file_id>[0-9]+)/open/(?P<filename>.+)$', pviews.ProblemFilesFileOpenView.as_view(), name='data_file_open'),
    url(r'^files/data/(?P<file_id>[0-9]+)/download/(?P<filename>.+)$', pviews.ProblemFilesFileOpenView.as_view(download=True), name='data_file_download'),
    url(r'^files/data/(?P<file_id>[0-9]+)/edit/$', pviews.ProblemFilesDataFileEditView.as_view(), name='data_file_edit'),
    url(r'^files/data/(?P<file_id>[0-9]+)/delete/$', pviews.ProblemFilesDataFileDeleteView.as_view(), name='data_file_delete'),
    url(r'^files/data/new/$', pviews.ProblemFilesDataFileNewView.as_view(), name='data_file_new'),

    url(r'^files/source/(?P<file_id>[0-9]+)/open/(?P<filename>.+)$', pviews.ProblemFilesSourceFileOpenView.as_view(), name='source_file_open'),
    url(r'^files/source/(?P<file_id>[0-9]+)/download/(?P<filename>.+)$', pviews.ProblemFilesSourceFileOpenView.as_view(download=True), name='source_file_download'),
    url(r'^files/source/(?P<file_id>[0-9]+)/edit/$', pviews.ProblemFilesSourceFileEditView.as_view(), name='source_file_edit'),
    url(r'^files/source/(?P<file_id>[0-9]+)/delete/$', pviews.ProblemFilesSourceFileDeleteView.as_view(), name='source_file_delete'),
    url(r'^files/source/new/$', pviews.ProblemFilesSourceFileNewView.as_view(), name='source_file_new'),

    url(r'^tex/$', pviews.ProblemTeXView.as_view(), name='tex'),
    url(r'^tex/render/$', pviews.ProblemTeXRenderView.as_view(), name='tex_render'),
    url(r'^tex/new/statement/$', pviews.ProblemTeXNewStatementView.as_view(), name='tex_new_statement'),
    url(r'^tex/new/statement/(?P<filename>.+)$', pviews.ProblemTeXEditorRelatedFileView.as_view()),
    url(r'^tex/(?P<file_id>[0-9]+)/$', pviews.ProblemTeXEditView.as_view(), name='edit_tex'),
    url(r'^tex/([0-9]+)/(?P<filename>.+)$', pviews.ProblemTeXEditorRelatedFileView.as_view()),

    url(r'^challenges/$', pviews.ProblemChallengesView.as_view(), name='challenges'),
    url(r'^challenges/(?P<challenge_id>[0-9]+)/$', pviews.ProblemChallengeView.as_view(), name='challenge'),
    url(r'^challenges/(?P<challenge_id>[0-9]+)/add-test/$', pviews.ProblemChallengeAddTestView.as_view(), name='challenge_add_test'),
    url(r'^challenges/(?P<challenge_id>[0-9]+)/status/json/$', pviews.ProblemChallengeJsonView.as_view(), name='challenge_status_json'),
    url(r'^challenges/(?P<challenge_id>[0-9]+)/open/(?P<resource_id>[0-9a-f]*)/(?P<filename>[a-z0-9\-]+)\.txt$', pviews.ProblemChallengeDataView.as_view(download=False), name='challenge_data_open'),
    url(r'^challenges/(?P<challenge_id>[0-9]+)/download/(?P<resource_id>[0-9a-f]*)/(?P<filename>[a-z0-9\-]+)\.txt$', pviews.ProblemChallengeDataView.as_view(download=True), name='challenge_data_download'),
    url(r'^challenges/new/$', pviews.ProblemNewChallengeView.as_view(), name='new_challenge'),

    url(r'^rejudges/$', pviews.ProblemRejudgesView.as_view(), name='rejudges'),

    url(r'^submit/$', pviews.ProblemSubmitView.as_view(), name='submit'),
    url(r'^submission/(?P<solution_id>[0-9]+)/$', pviews.ProblemSubmissionView.as_view(), name='submission'),
    url(r'^folders/$', pviews.ProblemFoldersView.as_view(), name='folders'),
    url(r'^name/$', pviews.ProblemNameView.as_view(), name='name'),
    url(r'^properties/$', pviews.ProblemPropertiesView.as_view(), name='properties'),
    url(r'^pictures/$', pviews.ProblemPicturesView.as_view(), name='pictures'),
    url(r'^validator/$', pviews.ProblemValidatorView.as_view(), name='validator'),
    url(r'^delete/$', pviews.ProblemDeleteView.as_view(), name='delete'),
    url(r'^access/$', pviews.ProblemAccessView.as_view(), name='access'),
]

urlpatterns = [
    url(r'^(?P<problem_id>[0-9]+)/', include(problem_urlpatterns)),
]

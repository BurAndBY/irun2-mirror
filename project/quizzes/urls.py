from django.conf.urls import include, url

from . import views
from .category import views as categoryviews
from .preview.urls import urlpatterns as preview_urlpatterns

group_urlpatterns = [
    url(r'^$', views.QuestionGroupListView.as_view(), name='list'),
    url(r'^new/$', views.QuestionGroupCreateView.as_view(), name='create'),
    url(r'^(?P<group_id>[0-9]+)/browse/$', views.QuestionGroupBrowseView.as_view(), name='browse'),
    url(r'^(?P<group_id>[0-9]+)/questions/(?P<question_id>[0-9]+)/edit/$', views.QuestionEditView.as_view(), name='edit_question'),
    url(r'^(?P<group_id>[0-9]+)/questions/new/$', views.QuestionCreateView.as_view(), name='create_question'),
    url(r'^(?P<group_id>[0-9]+)/questions/new/(?P<question_id>[0-9]+)/clone/$', views.QuestionCreateView.as_view(), name='clone_question'),
    url(r'^(?P<group_id>[0-9]+)/questions/upload/$', views.QuestionGroupUploadFromFileView.as_view(), name='upload'),
]

category_urlpatterns = [
    url(r'^$', categoryviews.CategoryListView.as_view(), name='list'),
    url(r'^new/$', categoryviews.CategoryCreateView.as_view(), name='create'),
    url(r'^(?P<categ_slug>[-\w]+)/edit/', categoryviews.CategoryUpdateView.as_view(), name='edit'),
    url(r'^(?P<categ_slug>[-\w]+)/access/', categoryviews.CategoryAccessView.as_view(), name='access'),
    url(r'^(?P<categ_slug>[-\w]+)/groups/', include(group_urlpatterns, namespace='groups')),
]

template_urlpatterns = [
    url(r'^$', views.QuizTemplateListView.as_view(), name='list'),
    url(r'^new/$', views.QuizTemplateCreateView.as_view(), name='create'),
    url(r'^(?P<pk>[0-9]+)/$', views.QuizTemplateDetailView.as_view(), name='detail'),
    url(r'^(?P<pk>[0-9]+)/edit/$', views.QuizTemplateUpdateView.as_view(), name='update'),
    url(r'^(?P<pk>[0-9]+)/edit-groups/$', views.QuizTemplateEditGroupsView.as_view(), name='edit_groups'),
    url(r'^(?P<pk>[0-9]+)/sessions/$', views.QuizSessionListView.as_view(), name='sessions'),
    url(r'^(?P<pk>[0-9]+)/statistics/$', views.QuizStatisticsView.as_view(), name='statistics'),
]

urlpatterns = [
    url(r'^$', views.EmptyView.as_view(), name='empty'),
    url(r'^quiz-templates/', include(template_urlpatterns, namespace='templates')),
    url(r'^categories/', include(category_urlpatterns, namespace='categories')),
    url(r'^preview/', include(preview_urlpatterns, namespace='preview')),
]

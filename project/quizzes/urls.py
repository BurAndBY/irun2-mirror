from django.conf.urls import include, url

from . import views

group_urlpatterns = [
    url(r'^$', views.QuestionGroupListView.as_view(), name='list'),
    url(r'^new/$', views.QuestionGroupCreateView.as_view(), name='create'),
    url(r'^(?P<pk>[0-9]+)/browse/$', views.QuestionGroupBrowseView.as_view(), name='browse'),
    url(r'^(?P<pk>[0-9]+)/questions/(?P<question_id>[0-9]+)/edit/$', views.QuestionEditView.as_view(), name='edit_question'),
    url(r'^(?P<pk>[0-9]+)/questions/new/$', views.QuestionCreateView.as_view(), name='create_question'),
]

template_urlpatterns = [
    url(r'^$', views.QuizTemplateListView.as_view(), name='list'),
    url(r'^new/$', views.QuizTemplateCreateView.as_view(), name='create'),
    url(r'^(?P<pk>[0-9]+)/$', views.QuizTemplateDetailView.as_view(), name='detail'),
    url(r'^(?P<pk>[0-9]+)/edit/$', views.QuizTemplateUpdateView.as_view(), name='update'),
    url(r'^(?P<pk>[0-9]+)/groups/add/$', views.QuizTemplateAddGroupView.as_view(), name='add_group'),
    url(r'^(?P<pk>[0-9]+)/groups/(?P<relation_id>[0-9]+)/delete/$', views.QuizTemplateDeleteGroupView.as_view(), name='delete_group'),
    url(r'^(?P<pk>[0-9]+)/sessions/$', views.QuizSessionListView.as_view(), name='sessions'),
    url(r'^(?P<pk>[0-9]+)/statistics/$', views.QuizStatisticsView.as_view(), name='statistics'),
]

urlpatterns = [
    url(r'^$', views.EmptyView.as_view(), name='empty'),
    url(r'^question-groups/', include(group_urlpatterns, namespace='groups')),
    url(r'^quiz-templates/', include(template_urlpatterns, namespace='templates')),
]

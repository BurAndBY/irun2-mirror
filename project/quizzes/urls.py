from django.conf.urls import include, url

from . import views

group_urlpatterns = [
    url(r'^$', views.QuestionGroupListView.as_view(), name='list'),
]

template_urlpatterns = [
    url(r'^$', views.QuizTemplateListView.as_view(), name='list'),
]

urlpatterns = [
    url(r'^$', views.EmptyView.as_view(), name='empty'),
    url(r'^question-groups/', include(group_urlpatterns, namespace='groups')),
    url(r'^quiz-templates/', include(template_urlpatterns, namespace='templates')),
]

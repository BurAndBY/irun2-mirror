from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^new/$', views.NewFeedbackView.as_view(), name='new'),
    url(r'^list/$', views.ListFeedbackView.as_view(), name='list'),
    url(r'^thanks/$', views.FeedbackThanksView.as_view(), name='thanks'),
    url(r'^(?P<message_id>[0-9]+)/attachment/(?P<filename>.*)$', views.FeedbackDownloadView.as_view(), name='download'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.FeedbackDeleteView.as_view(), name='delete'),
]

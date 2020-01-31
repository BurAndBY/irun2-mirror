from django.conf.urls import url

from . import views

app_name = 'news'

urlpatterns = [
    url(r'^new/$', views.CreateMessageView.as_view(), name='new'),
    url(r'^list/$', views.ListMessagesView.as_view(), name='list'),
    url(r'^(?P<pk>[0-9]+)/$', views.ShowMessageView.as_view(), name='show'),
    url(r'^(?P<pk>[0-9]+)/update/$', views.UpdateMessageView.as_view(), name='update'),
]

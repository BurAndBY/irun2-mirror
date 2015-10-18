from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^new/$', views.new, name='new'),
    url(r'^upload/$', views.upload, name='upload'),
    url(r'^resource/(?P<resource_id>[0-9a-f]*)/$', views.show, name='show'),
    url(r'^resource/(?P<resource_id>[0-9a-f]*)/download/$', views.download, name='download'),
]

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<user_id>[0-9]+)/card/$', views.UserCardView.as_view(), name='card'),
    url(r'^(?P<user_id>[0-9]+)/photo/(?P<resource_id>[0-9a-f]*)\.jpg$', views.PhotoView.as_view(), name='photo'),
]

from django.conf.urls import url

from django.contrib.auth import views as default_views
import views

urlpatterns = [
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', default_views.logout, name='logout'),
]

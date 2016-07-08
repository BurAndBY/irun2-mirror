from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^new/$', views.CreateCompilerView.as_view(), name='create'),
    url(r'^(?P<pk>[0-9]+)/$', views.UpdateCompilerView.as_view(), name='update'),
]

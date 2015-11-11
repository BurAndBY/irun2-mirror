from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^ad-hoc/$', views.AdHocView.as_view(), name='ad_hoc'),
    url(r'^$', views.SolutionListView.as_view(), name='list'),
]

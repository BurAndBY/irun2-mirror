from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.SolutionListView.as_view(), name='list'),
    url(r'^delete/$', views.DeleteSolutionsView.as_view(), name='delete'),
]

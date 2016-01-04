from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^folders/(?P<folder_id>root|[0-9]+)/$', views.ShowFolderView.as_view(), name='show_folder'),
    url(r'^folders/(?P<folder_id>root|[0-9]+)/create-subfolder/$', views.CreateFolderView.as_view(), name='create_folder'),
    url(r'^mass/$', views.MassUserCreateView.as_view(), name='mass_create'),
]

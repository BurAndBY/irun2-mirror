from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^list/$', views.IndexView.as_view(), name='index'),
    url(r'^folders/(?P<folder_id_or_root>root|[0-9]+)/$', views.ShowFolderView.as_view(), name='show_folder'),
    url(r'^folders/(?P<folder_id_or_root>root|[0-9]+)/create-folder/$', views.CreateFolderView.as_view(), name='create_folder'),
    url(r'^folders/(?P<folder_id_or_root>root|[0-9]+)/create-user/$', views.CreateUserView.as_view(), name='create_user'),
    url(r'^folders/(?P<folder_id_or_root>root|[0-9]+)/mass-registration/$', views.CreateUsersMassView.as_view(), name='create_users_mass'),
    url(r'^delete/$', views.DeleteUsersView.as_view(), name='delete'),
    url(r'^move/$', views.MoveUsersView.as_view(), name='move'),
]

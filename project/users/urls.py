from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^list/$', views.IndexView.as_view(), name='index'),
    url(r'^folders/(?P<folder_id_or_root>root|[0-9]+)/$', views.ShowFolderView.as_view(), name='show_folder'),
    url(r'^folders/(?P<folder_id_or_root>root|[0-9]+)/new/folder/$', views.CreateFolderView.as_view(), name='create_folder'),
    url(r'^folders/(?P<folder_id_or_root>root|[0-9]+)/new/user/$', views.CreateUserView.as_view(), name='create_user'),
    url(r'^folders/(?P<folder_id_or_root>root|[0-9]+)/bulk/sign-up/$', views.CreateUsersMassView.as_view(), name='create_users_mass'),
    url(r'^folders/(?P<folder_id_or_root>root|[0-9]+)/bulk/change-password/$', views.ChangePasswordMassView.as_view(), name='change_password_mass'),
    url(r'^delete/$', views.DeleteUsersView.as_view(), name='delete'),
    url(r'^move/$', views.MoveUsersView.as_view(), name='move'),
    url(r'^export\.json$', views.ExportView.as_view(), name='export'),
    url(r'^swap-first-last-name/$', views.SwapFirstLastNameView.as_view(), name='swap_first_last_name'),

    # single user profile
    url(r'^(?P<user_id>[0-9]+)/$', views.ProfileShowView.as_view(), name='profile_show'),
    url(r'^(?P<user_id>[0-9]+)/update/$', views.ProfileUpdateView.as_view(), name='profile_update'),
    url(r'^(?P<user_id>[0-9]+)/password/$', views.ProfilePasswordView.as_view(), name='profile_password'),
    url(r'^(?P<user_id>[0-9]+)/permissions/$', views.ProfilePermissionsView.as_view(), name='profile_permissions'),
    url(r'^(?P<user_id>[0-9]+)/photo/$', views.ProfilePhotoView.as_view(), name='profile_photo'),
    url(r'^(?P<user_id>[0-9]+)/card/$', views.UserCardView.as_view(), name='card'),
    url(r'^(?P<user_id>[0-9]+)/photo/(?P<resource_id>[0-9a-f]*)\.jpg$', views.PhotoView.as_view(), name='photo'),
]

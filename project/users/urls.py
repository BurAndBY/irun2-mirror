from django.conf.urls import include, url

from . import views

app_name = 'users'

folders_urlpatterns = [
    url(r'^$', views.ShowFolderView.as_view(), name='show_folder'),
    url(r'^new/folder/$', views.CreateFolderView.as_view(), name='create_folder'),
    url(r'^delete/$', views.DeleteFolderView.as_view(), name='delete_folder'),
    url(r'^new/user/$', views.CreateUserView.as_view(), name='create_user'),
    url(r'^bulk/sign-up/$', views.CreateUsersMassView.as_view(), name='create_users_mass'),
    url(r'^bulk/update-profile/$', views.UpdateProfileMassView.as_view(), name='update_profile_mass'),
    url(r'^bulk/upload-photo/$', views.UploadPhotoMassView.as_view(), name='upload_photo_mass'),
    url(r'^bulk/obtain-photos-from-intranet-bsu/$', views.ObtainPhotosFromIntranetBsuView.as_view(), name='obtain_intranet_bsu_photos'),
]

urlpatterns = [
    url(r'^list/$', views.IndexView.as_view(), name='index'),
    url(r'^folders/(?P<folder_id_or_root>root|[0-9]+)/', include(folders_urlpatterns)),
    url(r'^delete/$', views.DeleteUsersView.as_view(), name='delete'),
    url(r'^move/$', views.MoveUsersView.as_view(), name='move'),
    url(r'^export\.json$', views.ExportView.as_view(), name='export'),
    url(r'^swap-first-last-name/$', views.SwapFirstLastNameView.as_view(), name='swap_first_last_name'),

    # single user profile
    url(r'^(?P<user_id>[0-9]+)/$', views.ProfileShowView.as_view(), name='profile_show'),
    url(r'^(?P<user_id>[0-9]+)/main/$', views.ProfileMainView.as_view(), name='profile_main'),
    url(r'^(?P<user_id>[0-9]+)/update/$', views.ProfileUpdateView.as_view(), name='profile_update'),
    url(r'^(?P<user_id>[0-9]+)/password/$', views.ProfilePasswordView.as_view(), name='profile_password'),
    url(r'^(?P<user_id>[0-9]+)/two-factor/$', views.ProfileTwoFactorView.as_view(), name='profile_two_factor'),
    url(r'^(?P<user_id>[0-9]+)/permissions/$', views.ProfilePermissionsView.as_view(), name='profile_permissions'),
    url(r'^(?P<user_id>[0-9]+)/photo/$', views.ProfilePhotoView.as_view(), name='profile_photo'),
    url(r'^(?P<user_id>[0-9]+)/card/$', views.UserCardView.as_view(), name='card'),
    url(r'^(?P<user_id>[0-9]+)/photo/(?P<resource_id>[0-9a-f]*)\.jpg$', views.PhotoView.as_view(), name='photo'),
]

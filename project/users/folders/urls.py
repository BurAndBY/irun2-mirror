from django.conf.urls import url

from users.folders import views

urlpatterns = [
    url(r'^$', views.ShowFolderView.as_view(), name='show_folder'),
    url(r'^new/folder/$', views.CreateFolderView.as_view(), name='create_folder'),
    url(r'^delete/$', views.DeleteFolderView.as_view(), name='delete_folder'),
    url(r'^new/user/$', views.CreateUserView.as_view(), name='create_user'),
    url(r'^bulk/sign-up/$', views.CreateUsersMassView.as_view(), name='create_users_mass'),
    url(r'^bulk/update-profile/$', views.UpdateProfileMassView.as_view(), name='update_profile_mass'),
    url(r'^bulk/upload-photo/$', views.UploadPhotoMassView.as_view(), name='upload_photo_mass'),
    url(r'^bulk/obtain-photos-from-intranet-bsu/$', views.ObtainPhotosFromIntranetBsuView.as_view(), name='obtain_intranet_bsu_photos'),
]

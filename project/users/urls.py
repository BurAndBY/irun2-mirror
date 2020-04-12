from django.conf.urls import include, url

from . import views
from .admingroups.urls import admingroups_urlpatterns
from .folders.urls import urlpatterns as folders_urlpatterns

app_name = 'users'

urlpatterns = [
    url(r'^list/$', views.IndexView.as_view(), name='index'),
    url(r'^folders/(?P<folder_id_or_root>[^/]+)/', include(folders_urlpatterns)),
    url(r'^delete/$', views.DeleteUsersView.as_view(), name='delete'),
    url(r'^move/$', views.MoveUsersView.as_view(), name='move'),
    url(r'^export\.json$', views.ExportView.as_view(), name='export'),
    url(r'^swap-first-last-name/$', views.SwapFirstLastNameView.as_view(), name='swap_first_last_name'),
    url(r'^admin-groups/', include(admingroups_urlpatterns)),

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

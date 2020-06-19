from django.conf.urls import url

from . import views

urlpatterns = [
    # single user profile
    url(r'^(?P<user_id>[0-9]+)/$', views.ProfileShowView.as_view(), name='profile_show'),
    url(r'^(?P<user_id>[0-9]+)/main/$', views.ProfileMainView.as_view(), name='profile_main'),
    url(r'^(?P<user_id>[0-9]+)/update/$', views.ProfileUpdateView.as_view(), name='profile_update'),
    url(r'^(?P<user_id>[0-9]+)/password/$', views.ProfilePasswordView.as_view(), name='profile_password'),
    url(r'^(?P<user_id>[0-9]+)/two-factor/$', views.ProfileTwoFactorView.as_view(), name='profile_two_factor'),
    url(r'^(?P<user_id>[0-9]+)/permissions/$', views.ProfilePermissionsView.as_view(), name='profile_permissions'),
    url(r'^(?P<user_id>[0-9]+)/photo/$', views.ProfilePhotoView.as_view(), name='profile_photo'),
]

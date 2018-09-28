from django.conf.urls import include, url
from django.contrib.auth import views as default_views

from . import views
from . import twofactorviews
from . import overridden_views

two_factor_urlpatterns = [
    url(r'^profile/two-factor/$', twofactorviews.ProfileView.as_view(), name='profile'),
    url(r'^profile/two-factor/setup/$', twofactorviews.SetupView.as_view(), name='setup'),
    url(r'^profile/two-factor/setup/complete/$', twofactorviews.SetupCompleteView.as_view(), name='setup_complete'),
    url(r'^profile/two-factor/backup-tokens/$', twofactorviews.BackupTokensView.as_view(), name='backup_tokens'),
    url(r'^profile/two-factor/disable/$', twofactorviews.DisableView.as_view(), name='disable'),
    url(r'^profile/two-factor/qrcode/$', twofactorviews.QRGeneratorView.as_view(), name='qr'),
]

urlpatterns = [
    url(r'^login/$', twofactorviews.LoginView.as_view(), name='login'),
    url(r'^logout/$', default_views.logout, name='logout'),
    url(r'^profile/change-name/$', views.EditNameView.as_view(), name='name_change'),
    url(r'^profile/change-password/$', overridden_views.password_change, name='password_change'),
    url(r'^profile/change-password/done/$', default_views.password_change_done, name='password_change_done'),
    url(r'^profile/$', views.ShowProfileView.as_view(), name='profile'),
    url(r'^profile/edit/$', views.EditProfileView.as_view(), name='profile_edit'),

    url(r'^', include(two_factor_urlpatterns, namespace='two_factor')),
]

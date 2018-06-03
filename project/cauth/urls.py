from django.conf.urls import url

from django.contrib.auth import views as default_views
import views
import overridden_views

urlpatterns = [
    url(r'^login/$', overridden_views.login, name='login'),
    url(r'^logout/$', default_views.logout, name='logout'),
    url(r'^change-name/$', views.EditNameView.as_view(), name='name_change'),
    url(r'^change-password/$', overridden_views.password_change, name='password_change'),
    url(r'^change-password/done/$', default_views.password_change_done, name='password_change_done'),
    url(r'^profile/$', views.ShowProfileView.as_view(), name='profile'),
    url(r'^profile/edit/$', views.EditProfileView.as_view(), name='profile_edit'),
]

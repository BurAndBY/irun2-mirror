from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^mass/$', views.MassUserCreateView.as_view(), name='mass_create'),
]

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^language/$', views.language, name='language'),
    url(r'^about/', views.about, name='about'),
]

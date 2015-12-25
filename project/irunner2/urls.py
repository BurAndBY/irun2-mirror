"""irunner2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
#from django.contrib import admin
import common.views
from django_js_reverse.views import urls_js
from django.views.decorators.cache import cache_page


urlpatterns = [
    url(r'^$', common.views.home, name='home'),
    url(r'^feedback/', include('feedback.urls', namespace='feedback')),
    url(r'^i18n/', include('django.conf.urls.i18n'), name='set_language'),
    url(r'^demo/', include('demo.urls', namespace='demo')),
    url(r'^storage/', include('storage.urls', namespace='storage')),
    url(r'^problems/', include('problems.urls', namespace='problems')),
    url(r'^prog-langs/', include('proglangs.urls', namespace='proglangs')),
    url(r'^worker/', include('worker.urls', namespace='worker')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/', include('api.urls', namespace='api')),
    url(r'^solutions/', include('solutions.urls', namespace='solutions')),
    url(r'^courses/', include('courses.urls', namespace='courses')),
    url(r'^users/', include('users.urls', namespace='users')),
    url(r'^about/', common.views.about, name='about'),
    url(r'^choose/', common.views.choose, name='choose'),
    url(r'^list/(?P<folder_id>[0-9]+)/', common.views.listf, name='listf'),
    url('^', include('cauth.urls')),
    #url(r'^admin/', include(admin.site.urls)),
    url(r'^jsreverse/$', cache_page(3600)(urls_js), name='js_reverse'),
]

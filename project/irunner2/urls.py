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
    url(r'^language/$', common.views.language, name='language'),
    url(r'^feedback/', include('feedback.urls', namespace='feedback')),
    url(r'^news/', include('news.urls', namespace='news')),
    url(r'^i18n/', include('django.conf.urls.i18n'), name='set_language'),
    url(r'^storage/', include('storage.urls', namespace='storage')),
    url(r'^problems/', include('problems.urls', namespace='problems')),
    url(r'^compilers/', include('proglangs.urls', namespace='proglangs')),
    url(r'^api/', include('api.urls', namespace='api')),
    url(r'^', include('solutions.urls', namespace='solutions')),
    url(r'^courses/', include('courses.urls', namespace='courses')),
    url(r'^contests/', include('contests.urls', namespace='contests')),
    url(r'^users/', include('users.urls', namespace='users')),
    url(r'^about/', common.views.about, name='about'),
    url('^', include('cauth.urls')),
    #url(r'^admin/', include(admin.site.urls)),
    url(r'^jsreverse/$', cache_page(3600)(urls_js), name='js_reverse'),
    url(r'^hall-of-fame/$', common.views.HallOfFameView.as_view(), name='hall_of_fame')
]

handler403 = 'common.views.error403'

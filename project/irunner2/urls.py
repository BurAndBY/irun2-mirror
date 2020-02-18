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
from django.conf import settings
from django.conf.urls import include, url
from django_js_reverse.views import urls_js
from django.views.decorators.cache import cache_page

urlpatterns = [
    url(r'', include('cauth.urls')),
    url(r'', include('home.urls')),
    url(r'', include('solutions.urls', namespace='solutions')),
    url(r'^api/', include('api.urls', namespace='api')),
    url(r'^compilers/', include('proglangs.urls', namespace='proglangs')),
    url(r'^contests/', include('contests.urls', namespace='contests')),
    url(r'^courses/', include('courses.urls', namespace='courses')),
    url(r'^events/', include('events.urls', namespace='events')),
    url(r'^feedback/', include('feedback.urls', namespace='feedback')),
    url(r'^i18n/', include('django.conf.urls.i18n'), name='set_language'),
    url(r'^jsreverse/$', cache_page(3600)(urls_js), name='js_reverse'),
    url(r'^news/', include('news.urls', namespace='news')),
    url(r'^problems/', include('problems.urls', namespace='problems')),
    url(r'^quizzes/', include('quizzes.urls', namespace='quizzes')),
    url(r'^storage/', include('storage.urls', namespace='storage')),
    url(r'^users/', include('users.urls', namespace='users')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

handler403 = 'home.views.error403'

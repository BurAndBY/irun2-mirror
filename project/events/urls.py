from django.conf.urls import include, url

from . import views
from . import manageviews

# functionality for admins
manage_urlpatterns = [
    url(r'^$', manageviews.ListEventsView.as_view(), name='list'),
    url(r'^new/$', manageviews.CreateEventView.as_view(), name='new'),
    url(r'^update/(?P<slug>.*)/$', manageviews.UpdateEventView.as_view(), name='update'),
]

event_urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'', include('registration.urls')),
]

urlpatterns = [
    url(r'^manage/', include(manage_urlpatterns, namespace='manage')),
    url(r'^(?P<slug>[^/]+)/', include(event_urlpatterns)),
]

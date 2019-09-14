from django.conf.urls import include, url

from . import views
from . import manageviews

# functionality for admins
manage_urlpatterns = [
    url(r'^$', manageviews.ListEventsView.as_view(), name='list'),
    url(r'^new/$', manageviews.CreateEventView.as_view(), name='new'),
    url(r'^(?P<slug>.*)/update/$', manageviews.UpdateEventView.as_view(), name='update'),
    url(r'^(?P<slug>.*)/registration/$', manageviews.EventRegistrationView.as_view(), name='registration'),
    url(r'^(?P<slug>.*)/registration/teams\.csv$', manageviews.TeamsCsvView.as_view(), name='registration_csv'),
]

event_urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'', include('registration.urls')),
]

urlpatterns = [
    url(r'^manage/', include(manage_urlpatterns, namespace='manage')),
    url(r'^(?P<slug>[^/]+)/', include(event_urlpatterns)),
]

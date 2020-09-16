from django.conf.urls import include, url

from . import views
from . import manageviews

app_name = 'events'

# functionality for admins
manage_urlpatterns = ([
    url(r'^$', manageviews.ListEventsView.as_view(), name='list'),
    url(r'^new/$', manageviews.CreateEventView.as_view(), name='new'),
    url(r'^(?P<slug>.*)/update/$', manageviews.UpdateEventView.as_view(), name='update'),
    url(r'^(?P<slug>.*)/page-design/$', manageviews.EventPageDesignView.as_view(), name='page_design'),
    url(r'^(?P<slug>.*)/registration/$', manageviews.EventRegistrationView.as_view(), name='registration'),
    url(r'^(?P<slug>.*)/pages/$', manageviews.ListEventPagesView.as_view(), name='pages'),
    url(r'^(?P<slug>.*)/pages/new/$', manageviews.CreatePageView.as_view(), name='new_page'),
    url(r'^(?P<slug>.*)/pages/(?P<id>\d+)/$', manageviews.UpdatePageView.as_view(), name='update_page'),
    url(r'^(?P<slug>.*)/registration/teams\.csv$', manageviews.TeamsCsvView.as_view(), name='team_registration_csv'),
    url(r'^(?P<slug>.*)/registration/contestants\.csv$', manageviews.ContestantsCsvView.as_view(), name='contestant_registration_csv'),
], 'manage')

event_urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^pages/(?P<article_slug>.*)/$', views.PageView.as_view(), name='page'),
    url(r'^files/(?P<filename>.*)$', views.LogoView.as_view(), name='logo'),
    url(r'', include('registration.urls')),
]

urlpatterns = [
    url(r'^manage/', include(manage_urlpatterns)),
    url(r'^(?P<slug>[^/]+)/', include(event_urlpatterns)),
]

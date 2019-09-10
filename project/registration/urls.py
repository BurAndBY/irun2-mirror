from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^register/$', views.RegisterCoachView.as_view(), name='register_coach'),
    url(r'^register/(?P<coach_id>[^/]+)/$', views.ListTeamsView.as_view(), name='list_teams'),
    url(r'^register/(?P<coach_id>[^/]+)/teams/new/$', views.CreateTeamView.as_view(), name='create_team'),
    url(r'^register/(?P<coach_id>[^/]+)/teams/(?P<team_id>[0-9]+)/$', views.UpdateTeamView.as_view(), name='update_team'),
]

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.ChallengeListView.as_view(), name='challenge_list'),
]

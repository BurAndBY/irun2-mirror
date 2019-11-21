from django.conf.urls import include, url

from . import views
from .halloffame import views as hviews
from .activity import views as aviews
from .solution.urls import urlpatterns as solution_urlpatterns
from .judgement.urls import urlpatterns as judgement_urlpatterns

solutions_urlpatterns = [
    url(r'^$', views.SolutionListView.as_view(), name='list'),
    url(r'^delete/$', views.DeleteSolutionsView.as_view(), name='delete'),
    url(r'^compare/$', views.CompareSolutionsView.as_view(), name='compare'),
] + solution_urlpatterns

judgements_urlpatterns = [
    url(r'^$', views.JudgementListView.as_view(), name='judgement_list'),
] + judgement_urlpatterns

rejudges_urlpatterns = [
    url(r'^new/$', views.CreateRejudgeView.as_view(), name='create_rejudge'),
    url(r'^(?P<rejudge_id>[0-9]+)/$', views.RejudgeView.as_view(), name='rejudge'),
    url(r'^(?P<rejudge_id>[0-9]+)/status/json/$', views.RejudgeJsonView.as_view(), name='rejudge_status_json'),
    url(r'^$', views.RejudgeListView.as_view(), name='rejudge_list'),
]

challenges_urlpatterns = [
    url(r'^$', views.ChallengeListView.as_view(), name='challenge_list'),
]

urlpatterns = [
    url(r'^solutions/', include(solutions_urlpatterns)),
    url(r'^runs/', include(judgements_urlpatterns)),
    url(r'^rejudges/', include(rejudges_urlpatterns)),
    url(r'^challenges/', include(challenges_urlpatterns)),
    url(r'^hall-of-fame/$', hviews.HallOfFameView.as_view(), name='hall_of_fame'),
    url(r'^activity/$', aviews.ActivityView.as_view(), name='activity'),
]

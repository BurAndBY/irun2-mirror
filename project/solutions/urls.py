from django.conf.urls import include, url

from . import views
from .halloffame import views as hviews
from .activity import views as aviews
from .solution.urls import urlpatterns as solution_urlpatterns
from .judgement.urls import urlpatterns as judgement_urlpatterns
from .rejudge.urls import urlpatterns as rejudges_urlpatterns

app_name = 'solutions'

solutions_urlpatterns = [
    url(r'^$', views.SolutionListView.as_view(), name='list'),
    url(r'^delete/$', views.DeleteSolutionsView.as_view(), name='delete'),
    url(r'^compare/$', views.CompareSolutionsView.as_view(), name='compare'),
] + solution_urlpatterns

judgements_urlpatterns = [
    url(r'^$', views.JudgementListView.as_view(), name='judgement_list'),
] + judgement_urlpatterns

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

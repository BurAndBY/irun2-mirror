from django.conf.urls import include, url

from .halloffame import views as hviews
from .activity import views as aviews
from .challenges import views as chviews
from .compare import views as cmpviews

from .solution.urls import urlpatterns as solution_urlpatterns
from .solutions.urls import urlpatterns as solutions_urlpatterns
from .judgement.urls import urlpatterns as judgement_urlpatterns
from .rejudge.urls import urlpatterns as rejudges_urlpatterns

app_name = 'solutions'

urlpatterns = [
    url(r'^solutions/', include(solution_urlpatterns + solutions_urlpatterns)),
    url(r'^solutions/compare/$', cmpviews.CompareSolutionsView.as_view(), name='compare'),
    url(r'^runs/', include(judgement_urlpatterns)),
    url(r'^rejudges/', include(rejudges_urlpatterns)),
    url(r'^challenges/$', chviews.ChallengeListView.as_view(), name='challenge_list'),
    url(r'^hall-of-fame/$', hviews.HallOfFameView.as_view(), name='hall_of_fame'),
    url(r'^activity/$', aviews.ActivityView.as_view(), name='activity'),
]

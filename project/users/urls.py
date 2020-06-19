from django.conf.urls import include, url

from . import views
from .admingroups.urls import admingroups_urlpatterns
from .folders.urls import urlpatterns as folders_urlpatterns
from .card.urls import urlpatterns as card_urlpatterns
from .profile.urls import urlpatterns as profile_urlpatterns

app_name = 'users'

urlpatterns = [
    url(r'^list/$', views.IndexView.as_view(), name='index'),
    url(r'^folders/(?P<folder_id_or_root>[^/]+)/', include(folders_urlpatterns)),
    url(r'^delete/$', views.DeleteUsersView.as_view(), name='delete'),
    url(r'^move/$', views.MoveUsersView.as_view(), name='move'),
    url(r'^export\.json$', views.ExportView.as_view(), name='export'),
    url(r'^swap-first-last-name/$', views.SwapFirstLastNameView.as_view(), name='swap_first_last_name'),
    url(r'^admin-groups/', include(admingroups_urlpatterns)),
    url(r'', include(card_urlpatterns)),
    url(r'', include(profile_urlpatterns)),
]

from django.conf.urls import include, url

from problems import views
from problems.folders.urls import urlpatterns as folders_urlpatterns
from problems.problem.urls import urlpatterns as problem_urlpatterns

app_name = 'problems'

urlpatterns = [
    url(r'^$', views.DefaultView.as_view(), name='default'),
    url(r'^tree/$', views.ShowTreeView.as_view(), name='show_tree'),
    url(r'^tree/(?P<folder_id>[0-9]+)/$', views.ShowTreeFolderView.as_view(), name='show_tree_folder'),
    url(r'^tree/(?P<folder_id>[0-9]+)/json/$', views.ShowTreeFolderJsonView.as_view(), name='show_tree_folder_json'),
    url(r'^', include(problem_urlpatterns)),
    url(r'^folders/', include(folders_urlpatterns)),
    url(r'^search/$', views.SearchView.as_view(), name='search'),
    url(r'^tex/$', views.TeXView.as_view(), name='tex_playground'),
    url(r'^tex/render/$', views.TeXRenderView.as_view(), name='tex_playground_render'),
]

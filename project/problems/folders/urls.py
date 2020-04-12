from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<folder_id_or_root>[^/]+)/$', views.ShowFolderView.as_view(), name='show_folder'),
    url(r'^(?P<folder_id_or_root>[^/]+)/new/folder/$', views.CreateFolderView.as_view(), name='create_folder'),
    url(r'^(?P<folder_id_or_root>[^/]+)/new/problem/$', views.CreateProblemView.as_view(), name='create_problem'),
    url(r'^(?P<folder_id_or_root>[^/]+)/properties/$', views.UpdateFolderView.as_view(), name='folder_properties'),
    url(r'^(?P<folder_id_or_root>[^/]+)/access/$', views.FolderAccessView.as_view(), name='folder_access'),
    url(r'^(?P<folder_id_or_root>[^/]+)/delete/$', views.DeleteFolderView.as_view(), name='delete_folder'),
    url(r'^(?P<folder_id_or_root>[^/]+)/import-from-polygon/$', views.ImportFromPolygonView.as_view(), name='import_from_polygon'),
]

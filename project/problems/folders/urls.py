from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<folder_id_or_root>[0-9]+|root)/$', views.ShowFolderView.as_view(), name='show_folder'),
    url(r'^(?P<folder_id_or_root>[0-9]+|root)/new/folder/$', views.CreateFolderView.as_view(), name='create_folder'),
    url(r'^(?P<folder_id_or_root>[0-9]+|root)/new/problem/$', views.CreateProblemView.as_view(), name='create_problem'),
    url(r'^(?P<folder_id_or_root>[0-9]+|root)/properties/$', views.UpdateFolderView.as_view(), name='folder_properties'),
    url(r'^(?P<folder_id_or_root>[0-9]+|root)/access/$', views.FolderAccessView.as_view(), name='folder_access'),
    url(r'^(?P<folder_id_or_root>[0-9]+|root)/delete/$', views.DeleteFolderView.as_view(), name='delete_folder'),
    url(r'^(?P<folder_id_or_root>[0-9]+|root)/import-from-polygon/$', views.ImportFromPolygonView.as_view(), name='import_from_polygon'),
]

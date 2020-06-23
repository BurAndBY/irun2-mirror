from django.urls import path

from . import views

admingroups_urlpatterns = ([
    path('', views.ListView.as_view(), name='list'),
    path('new/', views.CreateView.as_view(), name='create'),
    path('<int:pk>/', views.UpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.DeleteView.as_view(), name='delete'),
    path('json/<str:folder_id_or_root>/', views.UsersJsonView.as_view(), name='users_json_list'),
], 'admingroups')

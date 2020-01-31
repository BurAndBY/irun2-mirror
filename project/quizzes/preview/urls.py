from django.conf.urls import url

from . import views

urlpatterns = ([
    url(r'^render$', views.RenderPreviewAPIView.as_view(), name='render'),
], 'preview')

from django.conf.urls import url

from . import views

app_name = 'tex'

urlpatterns = [
    # ex: /polls/
    url(r'^api/tex/render$', views.RenderTeXView.as_view(), name='render'),
]

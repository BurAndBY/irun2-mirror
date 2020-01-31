from django.conf.urls import url

from . import views

app_name = 'quizdemo'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^question/(?P<slug>[a-z\-]+)/(?P<seed>[0-9]+)/$', views.QuestionView.as_view(), name='question'),
]

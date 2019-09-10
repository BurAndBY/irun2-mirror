# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views import generic

from .models import Event


class HomeView(generic.DetailView):
    model = Event
    template_name = 'events/home.html'

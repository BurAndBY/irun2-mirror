# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.views import generic

from storage.models import FileMetadata
from storage.utils import serve_resource_metadata

from .models import Event


class HomeView(generic.DetailView):
    model = Event
    template_name = 'events/home.html'


class LogoView(generic.View):
    def get(self, request, slug, filename):
        metadata = get_object_or_404(FileMetadata, filename=filename, event__slug=slug)
        return serve_resource_metadata(request, metadata)

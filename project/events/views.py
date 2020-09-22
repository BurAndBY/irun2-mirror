# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, render, redirect
from django.views import generic

from common.pylightex import tex2html

from storage.models import FileMetadata
from storage.utils import serve_resource_metadata

from .models import Event


class HomeView(generic.DetailView):
    model = Event
    template_name = 'events/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        context['materials'] = event.page_set.order_by('when')
        context['content'] = tex2html(event.description)
        return context


class LogoView(generic.View):
    def get(self, request, slug, filename):
        metadata = get_object_or_404(FileMetadata, filename=filename, event__slug=slug)
        return serve_resource_metadata(request, metadata)


class PageView(generic.View):
    template_name = 'events/page.html'

    def get(self, request, slug, article_slug):
        event = get_object_or_404(Event, slug=slug)
        try:
            page = event.page_set.get(slug=article_slug, is_public=True)
        except ObjectDoesNotExist:
            return redirect('events:home', slug=slug)

        context = {
            'event': event,
            'page': page,
            'content': tex2html(page.content),
        }
        return render(request, self.template_name, context)

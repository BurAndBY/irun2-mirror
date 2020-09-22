# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import generic

from cauth.mixins import StaffMemberRequiredMixin

from .forms import PageDesignForm, PageForm, EventForm
from .models import Event, Page
from registration.models import IcpcCoach
from registration.export import make_teams_csv, make_contestants_csv


class ListEventsView(StaffMemberRequiredMixin, generic.ListView):
    model = Event
    template_name = 'events/manage/index.html'


class EventFormMixin(object):
    form_class = EventForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('events:manage:list')


class CreateEventView(StaffMemberRequiredMixin, EventFormMixin, generic.CreateView):
    model = Event
    template_name = 'events/manage/new.html'


class UpdateEventView(StaffMemberRequiredMixin, EventFormMixin, generic.UpdateView):
    model = Event
    template_name = 'events/manage/edit.html'


class EventPageDesignView(StaffMemberRequiredMixin, generic.UpdateView):
    model = Event
    form_class = PageDesignForm
    template_name = 'events/manage/edit.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['logo_file'].urlmaker = lambda fm: reverse('events:logo', args=(self.object.slug, fm.filename))
        return form

    def get_success_url(self):
        return reverse('events:manage:list')


class EventRegistrationView(StaffMemberRequiredMixin, generic.DetailView):
    model = Event
    template_name = 'events/manage/registration.html'

    def get_context_data(self, **kwargs):
        context = super(EventRegistrationView, self).get_context_data(**kwargs)
        event = self.object
        context['coaches'] = IcpcCoach.objects.filter(event=event).annotate(num_teams=Count('icpcteam'))
        return context


class EventMixin(object):
    def dispatch(self, request, slug, *args, **kwargs):
        self.event = get_object_or_404(Event, slug=slug)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event
        return context


class ListEventPagesView(StaffMemberRequiredMixin, EventMixin, generic.ListView):
    template_name = 'events/manage/pages/index.html'

    def get_queryset(self):
        return self.event.page_set.order_by('when')


class CreatePageView(StaffMemberRequiredMixin, EventMixin, generic.CreateView):
    model = Page
    template_name = 'events/manage/pages/new.html'
    form_class = PageForm

    def get_success_url(self):
        return reverse('events:manage:pages', kwargs={'slug': self.event.slug})

    def form_valid(self, form):
        form.instance.event = self.event
        return super().form_valid(form)


class UpdatePageView(StaffMemberRequiredMixin, EventMixin, generic.UpdateView):
    model = Page
    template_name = 'events/manage/pages/edit.html'
    form_class = PageForm

    def get_success_url(self):
        return reverse('events:manage:pages', kwargs={'slug': self.event.slug})

    def get_object(self):
        return get_object_or_404(self.event.page_set, id=self.kwargs['id'])


class TeamsCsvView(StaffMemberRequiredMixin, generic.detail.SingleObjectMixin, generic.View):
    model = Event

    def get(self, request, slug):
        event = self.get_object()
        return HttpResponse(make_teams_csv(event), content_type='text/csv; charset=utf-8')


class ContestantsCsvView(StaffMemberRequiredMixin, generic.detail.SingleObjectMixin, generic.View):
    model = Event

    def get(self, request, slug):
        event = self.get_object()
        return HttpResponse(make_contestants_csv(event), content_type='text/csv; charset=utf-8')

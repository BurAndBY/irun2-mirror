# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import HttpResponse
from django.views import generic

from cauth.mixins import StaffMemberRequiredMixin

from .models import Event
from registration.models import IcpcCoach
from registration.export import make_teams_csv

EVENT_FIELDS = ['slug', 'local_name', 'en_name', 'local_description', 'en_description', 'is_registration_available']


class ListEventsView(StaffMemberRequiredMixin, generic.ListView):
    model = Event
    template_name = 'events/manage/index.html'


class CreateEventView(StaffMemberRequiredMixin, generic.CreateView):
    model = Event
    template_name = 'events/manage/new.html'
    fields = EVENT_FIELDS

    def get_success_url(self):
        return reverse('events:manage:list')


class UpdateEventView(StaffMemberRequiredMixin, generic.UpdateView):
    model = Event
    template_name = 'events/manage/edit.html'
    fields = EVENT_FIELDS

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


class TeamsCsvView(StaffMemberRequiredMixin, generic.detail.SingleObjectMixin, generic.View):
    model = Event

    def get(self, request, slug):
        event = self.get_object()
        return HttpResponse(make_teams_csv(event), content_type='text/csv; charset=utf-8')

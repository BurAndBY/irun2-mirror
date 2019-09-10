# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.views import generic

from cauth.mixins import StaffMemberRequiredMixin

from .models import Event

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

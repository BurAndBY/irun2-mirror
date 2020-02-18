# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views import generic
from django.urls import reverse
from django.contrib import auth


from cauth.mixins import (
    LoginRequiredMixin,
    StaffMemberRequiredMixin
)
from users.models import AdminGroup

from .forms import AdminGroupForm
from .forms import (
    TwoPanelUserMultipleChoiceField,
)


class ListView(LoginRequiredMixin, generic.ListView):
    template_name = 'users/admingroups/list.html'

    @property
    def can_manage_groups(self):
        return self.request.user.is_staff

    def get_queryset(self):
        qs = AdminGroup.objects.prefetch_related('users')
        if not self.can_manage_groups:
            # show only my groups
            qs = qs.filter(users=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_manage_groups'] = self.can_manage_groups
        return context


class CreateView(StaffMemberRequiredMixin, generic.CreateView):
    model = AdminGroup
    fields = ['name']
    template_name = 'users/admingroups/create.html'

    def get_success_url(self):
        return reverse('users:admingroups:list')


class UpdateView(StaffMemberRequiredMixin, generic.UpdateView):
    model = AdminGroup
    form_class = AdminGroupForm
    template_name = 'users/admingroups/update.html'

    def get_success_url(self):
        return reverse('users:admingroups:list')


class DeleteView(StaffMemberRequiredMixin, generic.DeleteView):
    model = AdminGroup
    template_name = 'users/admingroups/delete.html'

    def get_success_url(self):
        return reverse('users:admingroups:list')


class UsersJsonView(StaffMemberRequiredMixin, generic.View):
    def get(self, request, folder_id):
        users = auth.get_user_model().objects.filter(userprofile__folder_id=folder_id)
        return TwoPanelUserMultipleChoiceField.ajax(users)

from __future__ import unicode_literals

import json
import operator
from six.moves import reduce

from django.contrib import auth
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, ProtectedError
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from cauth.mixins import AdminMemberRequiredMixin
from common.cast import make_int_list_quiet
from common.pagination import paginate
from common.views import MassOperationView

from users.forms import (
    UserSearchForm,
    MoveUsersForm,
)
from users.models import UserProfile
from users.profile.permissions import ProfilePermissions, ProfilePermissionCalcer
from users.profile.permissions import get_user_queryset


class IndexView(AdminMemberRequiredMixin, generic.View):
    template_name = 'users/index.html'
    paginate_by = 12

    def get_queryset(self, query=None, staff=False):
        queryset = get_user_queryset(self.request.user).select_related('userprofile').select_related('userprofile__folder')

        if query is not None:
            terms = query.split()
            if terms:
                search_args = []
                for term in terms:
                    search_args.append(Q(username__icontains=term) | Q(first_name__icontains=term) | Q(last_name__icontains=term))

                queryset = queryset.filter(reduce(operator.and_, search_args))

        if staff:
            queryset = queryset.filter(is_staff=True)

        queryset = queryset.order_by('id')
        return queryset

    def get(self, request):
        form = UserSearchForm(request.GET)
        if form.is_valid():
            queryset = self.get_queryset(form.cleaned_data['query'], form.cleaned_data['staff'])
        else:
            queryset = self.get_queryset()

        context = paginate(request, queryset, self.paginate_by)
        context['active_tab'] = 'search'
        context['form'] = form
        return render(request, self.template_name, context)


class DeleteUsersView(AdminMemberRequiredMixin, MassOperationView):
    template_name = 'users/bulk_operation.html'
    question = _('Are you sure you want to delete the users?')

    def get_queryset(self):
        return auth.get_user_model().objects

    def filter_objects(self, ids):
        return ProfilePermissionCalcer(self.request.user).filter_objects(ids, ProfilePermissions.EDIT)

    def perform(self, queryset, form):
        try:
            queryset.delete()
        except ProtectedError:
            messages.add_message(self.request, messages.ERROR, _('Unable to delete the users because they have related solutions.'))


class MoveUsersView(AdminMemberRequiredMixin, MassOperationView):
    template_name = 'users/bulk_operation.html'
    question = _('Are you sure you want to move the users to another folder?')
    form_class = MoveUsersForm

    def get_queryset(self):
        return UserProfile.objects.select_related('user')

    def filter_objects(self, ids):
        return ProfilePermissionCalcer(self.request.user).filter_objects(ids, ProfilePermissions.EDIT)

    def perform(self, queryset, form):
        folder = form.cleaned_data['folder']
        queryset.update(folder=folder)

    def prepare_to_display(self, userprofile):
        return userprofile.user

    def get_form_kwargs(self):
        return {'user': self.request.user}


class ExportView(AdminMemberRequiredMixin, generic.View):
    def get(self, request):
        user_ids = make_int_list_quiet(request.GET.getlist('id'))
        user_ids = ProfilePermissionCalcer(request.user).filter_objects(user_ids)
        users = []
        for user in auth.get_user_model().objects.filter(id__in=user_ids).select_related('userprofile'):
            users.append({
                'id': user.id,
                'username': user.username,
                'firstName': user.first_name,
                'lastName': user.last_name,
                'patronymic': user.userprofile.patronymic,
            })
        data = {'users': users}
        blob = json.dumps(data, ensure_ascii=False, indent=4)
        return HttpResponse(blob, content_type='application/json')


class SwapFirstLastNameView(AdminMemberRequiredMixin, MassOperationView):
    template_name = 'users/bulk_operation.html'
    question = _('Are you sure you want to swap first and last name of these users?')

    def get_queryset(self):
        return auth.get_user_model().objects

    def filter_objects(self, ids):
        return ProfilePermissionCalcer(self.request.user).filter_objects(ids, ProfilePermissions.EDIT)

    def perform(self, queryset, form):
        with transaction.atomic():
            for user in queryset:
                user.first_name, user.last_name = user.last_name, user.first_name
                user.save()

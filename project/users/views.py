from __future__ import unicode_literals

import json
import operator
from six.moves import reduce

from django.contrib import auth
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from django_otp import devices_for_user, user_has_device

from cauth.mixins import StaffMemberRequiredMixin
from common.cast import make_int_list_quiet
from common.fakefile import FakeFile
from common.pagination import paginate
from common.views import MassOperationView
from courses.models import Membership
from problems.models import ProblemAccess
from solutions.models import Solution
from storage.utils import create_storage, parse_resource_id, serve_resource

from users.forms import (
    UserSearchForm,
    MoveUsersForm,
    UserMainForm,
    UserForm,
    UserProfileMainForm,
    UserProfileForm,
    UserPermissionsForm,
    UserProfilePermissionsForm,
    PhotoForm,
)
from users.models import UserProfile


class IndexView(StaffMemberRequiredMixin, generic.View):
    template_name = 'users/index.html'
    paginate_by = 12

    def get_queryset(self, query=None, staff=False):
        queryset = auth.get_user_model().objects.all().select_related('userprofile').select_related('userprofile__folder')

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


class DeleteUsersView(StaffMemberRequiredMixin, MassOperationView):
    template_name = 'users/bulk_operation.html'
    question = _('Are you sure you want to delete the users?')

    def get_queryset(self):
        return auth.get_user_model().objects

    def perform(self, queryset, form):
        queryset.delete()


class MoveUsersView(StaffMemberRequiredMixin, MassOperationView):
    template_name = 'users/bulk_operation.html'
    question = _('Are you sure you want to move the users to another folder?')
    form_class = MoveUsersForm

    def get_queryset(self):
        return UserProfile.objects.select_related('user')

    def perform(self, queryset, form):
        folder = form.cleaned_data['folder']
        queryset.update(folder=folder)

    def prepare_to_display(self, userprofile):
        return userprofile.user


class ExportView(StaffMemberRequiredMixin, generic.View):
    def get(self, request):
        user_ids = make_int_list_quiet(request.GET.getlist('id'))
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


class SwapFirstLastNameView(StaffMemberRequiredMixin, MassOperationView):
    template_name = 'users/bulk_operation.html'
    question = _('Are you sure you want to swap first and last name of these users?')

    def get_queryset(self):
        return auth.get_user_model().objects

    def perform(self, queryset, form):
        with transaction.atomic():
            for user in queryset:
                user.first_name, user.last_name = user.last_name, user.first_name
                user.save()


class BaseProfileView(StaffMemberRequiredMixin):
    tab = None
    page_title = None

    def get_context_data(self, **kwargs):
        context = {
            'edited_user': self.user,
            'edited_profile': self.user.userprofile,
            'active_tab': self.tab,
        }
        if self.page_title is not None:
            context['page_title'] = self.page_title
        context.update(kwargs)
        return context

    def dispatch(self, request, user_id, *args, **kwargs):
        user = get_object_or_404(auth.get_user_model(), pk=user_id)
        self.user = user
        return super(BaseProfileView, self).dispatch(request, user, *args, **kwargs)


class ProfileShowView(BaseProfileView, generic.View):
    tab = 'show'
    template_name = 'users/profile_show.html'

    def get(self, request, user):
        num_solutions = Solution.objects.filter(author=user).count()
        context = self.get_context_data(num_solutions=num_solutions)
        return render(request, self.template_name, context)


class ProfileTwoFormsView(BaseProfileView, generic.View):
    user_form_class = None
    userprofile_form_class = None

    def get(self, request, user):
        user_form = self.user_form_class(instance=user)
        userprofile_form = self.userprofile_form_class(instance=user.userprofile)
        return render(request, self.template_name, self.get_context_data(user_form=user_form, userprofile_form=userprofile_form))

    def post(self, request, user):
        user_form = self.user_form_class(request.POST, instance=user)
        userprofile_form = self.userprofile_form_class(request.POST, instance=user.userprofile)

        if user_form.is_valid() and userprofile_form.is_valid():
            with transaction.atomic():
                user_form.save()
                userprofile_form.save()
            return redirect('users:profile_show', user.id)

        return render(request, self.template_name, self.get_context_data(user_form=user_form, userprofile_form=userprofile_form))


class ProfileMainView(ProfileTwoFormsView):
    tab = 'main'
    template_name = 'users/profile_update.html'
    user_form_class = UserMainForm
    userprofile_form_class = UserProfileMainForm
    page_title = _('Main properties')


class ProfileUpdateView(ProfileTwoFormsView):
    tab = 'update'
    template_name = 'users/profile_update.html'
    user_form_class = UserForm
    userprofile_form_class = UserProfileForm
    page_title = _('Update profile')


class ProfilePasswordView(BaseProfileView, generic.View):
    tab = 'password'
    template_name = 'users/profile_password.html'
    page_title = _('Change password')

    def get(self, request, user):
        form = auth.forms.AdminPasswordChangeForm(user)
        return render(request, self.template_name, self.get_context_data(form=form))

    def post(self, request, user):
        form = auth.forms.AdminPasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            return redirect('users:profile_show', user.id)
        return render(request, self.template_name, self.get_context_data(form=form))


class ProfilePermissionsView(ProfileTwoFormsView):
    tab = 'permissions'
    template_name = 'users/profile_update.html'
    user_form_class = UserPermissionsForm
    userprofile_form_class = UserProfilePermissionsForm
    page_title = _('Permissions')


class ProfilePhotoView(BaseProfileView, generic.View):
    tab = 'photo'
    template_name = 'users/profile_photo.html'
    page_title = _('Photo')

    def _make_form(self, profile, data=None, files=None):
        if profile.photo is not None:
            url = reverse('users:photo', kwargs={'user_id': profile.user_id, 'resource_id': profile.photo})
            name = ugettext('Photo')
            f = FakeFile(url, name)
        else:
            f = None
        form = PhotoForm(data=data, files=files, initial={'upload': f})
        return form

    def get(self, request, user):
        form = self._make_form(user.userprofile)
        context = self.get_context_data(form=form, profile=user.userprofile)
        return render(request, self.template_name, context)

    def post(self, request, user):
        profile = user.userprofile
        form = self._make_form(user.userprofile, request.POST, request.FILES)
        if form.is_valid():
            upload = form.cleaned_data['upload']

            if not upload:
                profile.photo = None
                profile.photo_thumbnail = None
                profile.save()
            elif type(upload) is FakeFile:
                # do not change existing file
                pass
            else:
                storage = create_storage()
                profile.photo = storage.save(upload)
                profile.photo_thumbnail = storage.save(form.cleaned_data['thumbnail'])
                profile.save()

            return redirect('users:profile_photo', user_id=user.id)

        context = self.get_context_data(form=form, profile=profile)
        return render(request, self.template_name, context)


class ProfileTwoFactorView(BaseProfileView, generic.View):
    tab = 'two_factor'
    template_name = 'users/profile_two_factor.html'
    page_title = _('Two-factor authentication')

    def get(self, request, user):
        return render(request, self.template_name,
                      self.get_context_data(enabled=user_has_device(user)))

    def post(self, request, user):
        with transaction.atomic():
            for device in devices_for_user(user):
                device.delete()
        return redirect('users:profile_two_factor', user.id)


def is_allowed(request_user, target_user):
    if not request_user.is_authenticated:
        return False
    if request_user == target_user:
        return True
    if request_user.is_staff or target_user.is_staff:
        return True

    def get_courses(user):
        return set(Membership.objects.filter(user=user).values_list('course_id', flat=True))

    if get_courses(request_user) & get_courses(target_user):
        return True

    if ProblemAccess.objects.filter(user=request_user, problem__solution__author=target_user).exists():
        return True

    return False


class UserCardView(generic.View):
    max_memberships = 10
    template_name = 'users/user_card.html'

    def get(self, request, user_id):
        user = get_object_or_404(auth.get_user_model(), pk=user_id)
        if not is_allowed(request.user, user):
            return HttpResponseForbidden()
        profile = user.userprofile
        course_memberships = Membership.objects.filter(user=user, role=Membership.STUDENT).\
            select_related('course', 'subgroup').\
            order_by('-id')[:self.max_memberships]

        context = {
            'user': user,
            'profile': profile,
            'course_memberships': course_memberships,
        }
        return render(request, self.template_name, context)


class PhotoView(generic.View):
    def get(self, request, user_id, resource_id):
        resource_id = parse_resource_id(resource_id)
        valid_ids = UserProfile.objects.filter(user_id=user_id).values_list('photo', 'photo_thumbnail').first()
        if (valid_ids is not None) and (resource_id in valid_ids):
            return serve_resource(request, resource_id, content_type='image/jpeg', cache_forever=True)
        raise Http404('User or photo was not found.')

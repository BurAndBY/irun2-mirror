from __future__ import unicode_literals

from django.contrib import auth
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from django_otp import devices_for_user, user_has_device

from common.fakefile import FakeFile
from solutions.models import Solution
from storage.utils import create_storage

from users.profile.permissions import ProfilePermissions
from users.profile.mixins import ProfilePermissionCheckMixin
from users.profile.forms import (
    UserMainForm,
    UserForm,
    UserProfileMainForm,
    UserProfileForm,
    UserPermissionsForm,
    UserProfilePermissionsForm,
    PhotoForm,
)


class BaseProfileView(ProfilePermissionCheckMixin, generic.base.ContextMixin):
    tab = None
    page_title = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**{
            'edited_user': self.user,
            'edited_profile': self.user.userprofile,
            'active_tab': self.tab,
        })
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_post_form'] = self._can_handle_post_request()
        return context

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
    requirements_to_post = ProfilePermissions.EDIT


class ProfileUpdateView(ProfileTwoFormsView):
    tab = 'update'
    template_name = 'users/profile_update.html'
    user_form_class = UserForm
    userprofile_form_class = UserProfileForm
    page_title = _('Update profile')
    requirements_to_post = ProfilePermissions.EDIT


class ProfilePasswordView(BaseProfileView, generic.View):
    tab = 'password'
    template_name = 'users/profile_password.html'
    page_title = _('Change password')
    requirements = ProfilePermissions.EDIT

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
    requirements_to_post = ProfilePermissions.JOIN_TO_STAFF


class ProfilePhotoView(BaseProfileView, generic.View):
    tab = 'photo'
    template_name = 'users/profile_photo.html'
    page_title = _('Photo')
    requirements = ProfilePermissions.EDIT

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
    requirements_to_post = ProfilePermissions.EDIT

    def get(self, request, user):
        return render(request, self.template_name,
                      self.get_context_data(enabled=user_has_device(user)))

    def post(self, request, user):
        with transaction.atomic():
            for device in devices_for_user(user):
                device.delete()
        return redirect('users:profile_two_factor', user.id)

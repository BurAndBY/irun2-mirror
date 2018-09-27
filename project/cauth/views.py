from django.db import transaction
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views import generic

from cauth.mixins import LoginRequiredMixin, UserPassesTestMixin
from cauth import forms


class ShowProfileView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'cauth/profile.html'

    def get_context_data(self, **kwargs):
        context = super(ShowProfileView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        profile = self.request.user.userprofile
        context['show_photo'] = not profile.is_team()
        context['can_change_name'] = profile.can_change_name
        context['can_change_password'] = profile.can_change_password
        return context


class CanChangeNameMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.userprofile.can_change_name


class EditNameView(LoginRequiredMixin, CanChangeNameMixin, generic.View):
    template_name = 'cauth/profile_edit.html'

    def get_context_data(self, user_form, userprofile_form):
        return {
            'user_form': user_form,
            'userprofile_form': userprofile_form,
        }

    def get(self, request):
        user_form = forms.UserNameForm(instance=request.user)
        userprofile_form = forms.UserProfileNameForm(instance=request.user.userprofile)

        return render(request, self.template_name, self.get_context_data(user_form, userprofile_form))

    def post(self, request):
        user_form = forms.UserNameForm(request.POST, instance=request.user)
        userprofile_form = forms.UserProfileNameForm(request.POST, instance=request.user.userprofile)

        if user_form.is_valid() and userprofile_form.is_valid():
            with transaction.atomic():
                user_form.save()
                userprofile_form.save()
                return redirect('profile')

        return render(request, self.template_name, self.get_context_data(user_form, userprofile_form))


class EditProfileView(LoginRequiredMixin, generic.UpdateView):
    template_name = 'cauth/profile_edit.html'
    form_class = forms.UserForm

    def get_context_data(self, **kwargs):
        context = super(EditProfileView, self).get_context_data(**kwargs)
        context['user_form'] = self.get_form()
        return context

    def get_success_url(self):
        return reverse('profile')

    def get_object(self):
        return self.request.user


class CanChangePasswordMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.userprofile.can_change_password

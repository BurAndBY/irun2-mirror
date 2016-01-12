from django.views import generic

from common.views import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, render_to_response, redirect
from django.db import transaction

import forms


class ShowProfileView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'cauth/profile.html'

    def get_context_data(self, **kwargs):
        context = super(ShowProfileView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class EditProfileView(LoginRequiredMixin, generic.View):
    template_name = 'cauth/profile_edit.html'

    def get_context_data(self, user_form, userprofile_form):
        return {
            'user_form': user_form,
            'userprofile_form': userprofile_form,
        }

    def get(self, request):
        user_form = forms.UserForm(instance=request.user)
        userprofile_form = forms.UserProfileForm(instance=request.user.userprofile)

        return render(request, self.template_name, self.get_context_data(user_form, userprofile_form))

    def post(self, request):
        user_form = forms.UserForm(request.POST, instance=request.user)
        userprofile_form = forms.UserProfileForm(request.POST, instance=request.user.userprofile)

        if user_form.is_valid() and userprofile_form.is_valid():
            with transaction.atomic():
                user_form.save()
                userprofile_form.save()
                return redirect('profile')

        return render(request, self.template_name, self.get_context_data(user_form, userprofile_form))

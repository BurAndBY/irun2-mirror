import operator

from django.contrib import auth, messages
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext
from django.views import generic
from django.http import HttpResponse

from cauth.mixins import StaffMemberRequiredMixin
from common.folderutils import lookup_node_ex, cast_id
from common.pageutils import paginate
from common.views import IRunnerListView, MassOperationView
from courses.models import Membership
from solutions.models import Solution

import forms
from models import UserFolder, UserProfile


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
        form = forms.UserSearchForm(request.GET)
        if form.is_valid():
            queryset = self.get_queryset(form.cleaned_data['query'], form.cleaned_data['staff'])
        else:
            queryset = self.get_queryset()

        context = paginate(request, queryset, self.paginate_by)
        context['active_tab'] = 'search'
        context['form'] = form
        return render(request, self.template_name, context)


class UserFolderMixin(object):
    def get_context_data(self, **kwargs):
        context = super(UserFolderMixin, self).get_context_data(**kwargs)
        cached_trees = UserFolder.objects.all().get_cached_trees()
        node_ex = lookup_node_ex(self.kwargs['folder_id_or_root'], cached_trees)

        context['cached_trees'] = cached_trees
        context['folder'] = node_ex.object
        context['folder_id'] = node_ex.folder_id
        context['active_tab'] = 'folders'
        return context


class ShowFolderView(StaffMemberRequiredMixin, UserFolderMixin, IRunnerListView):
    template_name = 'users/folder.html'
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super(ShowFolderView, self).get_context_data(**kwargs)

        folder = context['folder']

        has_users = (self.get_queryset().count() > 0)
        can_delete_folder = (not has_users) and (folder is not None) and (folder.get_descendant_count() == 0)

        context['has_users'] = has_users
        context['can_delete_folder'] = can_delete_folder
        return context

    def get_queryset(self):
        folder_id = cast_id(self.kwargs['folder_id_or_root'])
        return auth.get_user_model().objects.filter(userprofile__folder_id=folder_id)


class CreateFolderView(StaffMemberRequiredMixin, UserFolderMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = forms.CreateFolderForm

    def get_context_data(self, **kwargs):
        context = super(CreateFolderView, self).get_context_data(**kwargs)
        context['form_name'] = _('Create folder')
        return context

    def form_valid(self, form):
        folder_id_or_root = self.kwargs['folder_id_or_root']
        folder_id = cast_id(folder_id_or_root)
        UserFolder.objects.create(name=form.cleaned_data['name'], parent_id=folder_id)
        return redirect('users:show_folder', folder_id_or_root)


class CreateUserView(StaffMemberRequiredMixin, UserFolderMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = forms.CreateUserForm

    def get_context_data(self, **kwargs):
        context = super(CreateUserView, self).get_context_data(**kwargs)
        context['form_name'] = _('Create user')
        return context

    def form_valid(self, form):
        folder_id_or_root = self.kwargs['folder_id_or_root']
        folder_id = cast_id(folder_id_or_root)
        with transaction.atomic():
            user = form.save()
            profile = user.userprofile
            profile.folder_id = folder_id
            profile.save()
        return redirect('users:show_folder', folder_id_or_root)


class CreateUsersMassView(StaffMemberRequiredMixin, UserFolderMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = forms.CreateUsersMassForm
    initial = {'password': '11111'}

    def get_context_data(self, **kwargs):
        context = super(CreateUsersMassView, self).get_context_data(**kwargs)
        context['form_name'] = _('Bulk sign-up')
        return context

    def form_valid(self, form):
        folder_id_or_root = self.kwargs['folder_id_or_root']
        folder_id = cast_id(folder_id_or_root)
        pairs = form.cleaned_data['pairs']
        counter = 0
        with transaction.atomic():
            for user, userprofile in pairs:
                user.save()
                userprofile.user = user
                userprofile.folder_id = folder_id
                userprofile.save()
                counter += 1

        msg = ungettext('%(count)d user was added.', '%(count)d users were added.', counter) % {'count': counter}
        messages.add_message(self.request, messages.INFO, msg)
        return redirect('users:show_folder', folder_id_or_root)


class ChangePasswordMassView(StaffMemberRequiredMixin, UserFolderMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = forms.ChangePasswordMassForm

    def get_context_data(self, **kwargs):
        context = super(ChangePasswordMassView, self).get_context_data(**kwargs)
        context['form_name'] = _('Bulk password change')
        return context

    def get_form_kwargs(self):
        kwargs = super(ChangePasswordMassView, self).get_form_kwargs()
        folder_id_or_root = self.kwargs['folder_id_or_root']
        folder_id = cast_id(folder_id_or_root)
        kwargs['folder_id'] = folder_id
        return kwargs

    def form_valid(self, form):
        folder_id_or_root = self.kwargs['folder_id_or_root']
        pairs = form.cleaned_data['tsv']
        counter = 0
        with transaction.atomic():
            for username, password in pairs:
                # use weak hashing algorithm for better performance
                hashed_password = make_password(password, None, 'md5')
                counter += auth.get_user_model().objects.filter(username=username).update(password=hashed_password)
                UserProfile.objects.filter(user__username=username).update(needs_change_password=False)

        msg = ungettext('%(count)d password has been changed.', '%(count)d passwords have been changed.', counter) % {'count': counter}
        messages.add_message(self.request, messages.INFO, msg)
        return redirect('users:show_folder', folder_id_or_root)


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
    form_class = forms.MoveUsersForm

    def get_queryset(self):
        return UserProfile.objects.select_related('user')

    def perform(self, queryset, form):
        folder = form.cleaned_data['folder']
        queryset.update(folder=folder)

    def prepare_to_display(self, userprofile):
        return userprofile.user


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

    def get_context_data(self, **kwargs):
        context = {
            'edited_user': self.user,
            'edited_profile': self.user.userprofile,
            'active_tab': self.tab,
        }
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


class ProfileUpdateView(ProfileTwoFormsView):
    tab = 'update'
    template_name = 'users/profile_update.html'
    user_form_class = forms.UserForm
    userprofile_form_class = forms.UserProfileForm

    def get_context_data(self, **kwargs):
        context = super(ProfileUpdateView, self).get_context_data(**kwargs)
        context['page_title'] = _('Update profile')
        return context


class ProfilePasswordView(BaseProfileView, generic.View):
    tab = 'password'
    template_name = 'users/profile_password.html'

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
    user_form_class = forms.UserPermissionsForm
    userprofile_form_class = forms.UserProfilePermissionsForm

    def get_context_data(self, **kwargs):
        context = super(ProfilePermissionsView, self).get_context_data(**kwargs)
        context['page_title'] = _('Permissions')
        return context


class UserCardView(StaffMemberRequiredMixin, generic.View):
    max_memberships = 10
    template_name = 'users/user_card.html'

    def get(self, request, user_id):
        user = get_object_or_404(auth.get_user_model(), pk=user_id)
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

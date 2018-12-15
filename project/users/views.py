from __future__ import unicode_literals

import json
import operator
from collections import namedtuple
from six.moves import reduce

from django.contrib import auth, messages
from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.encoding import smart_text
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext
from django.views import generic
from django.http import HttpResponse, Http404

from django_otp import devices_for_user, user_has_device

from cauth.mixins import StaffMemberRequiredMixin
from common.cast import make_int_list_quiet
from common.fakefile import FakeFile
from common.folderutils import lookup_node_ex, cast_id, ROOT
from common.pageutils import paginate
from common.views import IRunnerListView, MassOperationView
from courses.models import Membership
from problems.models import ProblemAccess
from solutions.models import Solution
from storage.utils import create_storage, parse_resource_id, serve_resource

from users import forms
from users.models import UserFolder, UserProfile
import users.intranetbsu as intranetbsu
import users.intranetbsu.photos as intranetbsuphotos
import users.photo as photo


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


class DeleteFolderView(StaffMemberRequiredMixin, UserFolderMixin, generic.base.ContextMixin, generic.View):
    template_name = 'users/folder_confirm_delete.html'

    def get(self, request, folder_id_or_root):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, folder_id_or_root):
        folder_id = cast_id(folder_id_or_root)
        folder = get_object_or_404(UserFolder, pk=folder_id)
        parent_id = folder.parent_id
        with transaction.atomic():
            # TODO: check that it is empty, ...
            if (folder.get_descendant_count() == 0) and (not folder.userprofile_set.exists()):
                folder.delete()
        return redirect('users:show_folder', parent_id if parent_id is not None else ROOT)


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


class UpdateProfileMassView(StaffMemberRequiredMixin, UserFolderMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = forms.UpdateProfileMassForm

    def get_context_data(self, **kwargs):
        context = super(UpdateProfileMassView, self).get_context_data(**kwargs)
        context['form_name'] = _('Bulk profile update')
        return context

    def get_form_kwargs(self):
        kwargs = super(UpdateProfileMassView, self).get_form_kwargs()
        folder_id_or_root = self.kwargs['folder_id_or_root']
        folder_id = cast_id(folder_id_or_root)
        kwargs['folder_id'] = folder_id
        return kwargs

    def form_valid(self, form):
        folder_id_or_root = self.kwargs['folder_id_or_root']
        pairs = form.cleaned_data['tsv']
        counter = 0
        field = form.cleaned_data['field']
        with transaction.atomic():
            if field == 'password':
                for user_id, password in pairs:
                    # use weak hashing algorithm for better performance
                    hashed_password = make_password(password, None, 'md5')
                    counter += auth.get_user_model().objects.filter(pk=user_id).update(password=hashed_password)
                    UserProfile.objects.filter(pk=user_id).update(needs_change_password=False)

            elif field == 'team_name':
                for user_id, name in pairs:
                    UserProfile.objects.filter(pk=user_id).update(kind=UserProfile.TEAM)
                    counter += auth.get_user_model().objects.filter(pk=user_id).update(first_name=name, last_name='')

            elif field == 'team_members':
                for user_id, members in pairs:
                    counter += UserProfile.objects.filter(pk=user_id).update(kind=UserProfile.TEAM, members=members)

            elif field == 'full_name':
                for user_id, full_name in pairs:
                    tokens = full_name.split(None, 2)
                    while len(tokens) < 3:
                        tokens.append('')

                    counter += UserProfile.objects.filter(pk=user_id).update(kind=UserProfile.PERSON, patronymic=tokens[2])
                    auth.get_user_model().objects.filter(pk=user_id).update(last_name=tokens[0], first_name=tokens[1])

        msg = ungettext('%(count)d profile has been updated.', '%(count)d profiles have been updated.', counter) % {'count': counter}
        messages.add_message(self.request, messages.INFO, msg)
        return redirect('users:show_folder', folder_id_or_root)


class UploadPhotoMassView(StaffMemberRequiredMixin, UserFolderMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = forms.UploadPhotoMassForm

    def get_context_data(self, **kwargs):
        context = super(UploadPhotoMassView, self).get_context_data(**kwargs)
        context['form_name'] = _('Bulk photo upload')
        return context

    def get_form_kwargs(self):
        kwargs = super(UploadPhotoMassView, self).get_form_kwargs()
        folder_id_or_root = self.kwargs['folder_id_or_root']
        folder_id = cast_id(folder_id_or_root)
        kwargs['folder_id'] = folder_id
        return kwargs

    def form_valid(self, form):
        folder_id_or_root = self.kwargs['folder_id_or_root']
        upload = form.cleaned_data['upload']
        counter = 0
        storage = create_storage()

        with transaction.atomic():
            for user_id, photos in upload.iteritems():
                photo, photo_thumbnail = photos
                photo_id = storage.save(ContentFile(photo))
                photo_thumbnail_id = storage.save(ContentFile(photo_thumbnail))
                counter += UserProfile.objects.filter(pk=user_id).update(photo=photo_id, photo_thumbnail=photo_thumbnail_id)

        msg = ungettext('%(count)d photo has been uploaded.', '%(count)d photos have been uploaded.', counter) % {'count': counter}
        messages.add_message(self.request, messages.INFO, msg)
        return redirect('users:show_folder', folder_id_or_root)


class ObtainPhotosFromIntranetBsuView(StaffMemberRequiredMixin, UserFolderMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = forms.IntranetBsuForm

    UserError = namedtuple('UserError', 'user type message')
    PhotoIds = namedtuple('PhotoIds', 'photo photo_thumbnail')

    def get_context_data(self, **kwargs):
        context = super(ObtainPhotosFromIntranetBsuView, self).get_context_data(**kwargs)
        context['form_name'] = _('Photos from intranet.bsu')
        return context

    def _get_initial_group(self):
        folder_id_or_root = self.kwargs['folder_id_or_root']
        if folder_id_or_root is None:
            return
        folder = UserFolder.objects.filter(pk=folder_id_or_root).first()
        if folder is None:
            return
        return intranetbsu.extract_group(folder.name)

    def get_initial(self):
        initial = {}
        group = self._get_initial_group()
        if group is not None:
            initial['group'] = group
        return initial

    def form_valid(self, form):
        folder_id_or_root = self.kwargs['folder_id_or_root']
        folder_id = cast_id(folder_id_or_root)

        counter = 0
        photo_ids = {}
        storage = create_storage()

        errors = []
        skip_errors = form.cleaned_data['skip_errors']

        for user in auth.get_user_model().objects.filter(userprofile__folder_id=folder_id).select_related('userprofile'):
            if user.userprofile.photo is not None:
                continue

            request = intranetbsuphotos.Request(
                form.cleaned_data['faculty'],
                user.first_name,
                user.last_name,
                user.userprofile.patronymic
            )
            request.admission_year = form.cleaned_data['admission_year']
            request.include_archive = form.cleaned_data['include_archive']
            request.group = form.cleaned_data['group']

            photo_blob = None
            photo_thumbnail_blob = None

            try:
                # photo.generate_thumbnail_blob(None)
                photo_blob = intranetbsuphotos.download_photo(request)
                if photo_blob is not None:
                    photo_thumbnail_blob = photo.generate_thumbnail_blob(photo_blob)
            except Exception as e:
                message = e.message
                if not message:
                    message = smart_text(e)
                errors.append(self.UserError(user, type(e).__name__, message))
                if not skip_errors:
                    return self.error_page(errors)

            if photo_blob is not None and photo_thumbnail_blob is not None:
                photo_ids[user.id] = self.PhotoIds(
                    storage.save(ContentFile(photo_blob)),
                    storage.save(ContentFile(photo_thumbnail_blob))
                )

        with transaction.atomic():
            for user_id, ids in photo_ids.iteritems():
                counter += UserProfile.objects.filter(pk=user_id).update(photo=ids.photo, photo_thumbnail=ids.photo_thumbnail)

        msg = ungettext('%(count)d photo has been uploaded.', '%(count)d photos have been uploaded.', counter) % {'count': counter}
        messages.add_message(self.request, messages.INFO, msg)

        if errors:
            return self.error_page(errors)
        else:
            return redirect('users:show_folder', folder_id_or_root)

    def error_page(self, errors):
        template_name = 'users/intranetbsu_errors.html'
        context = self.get_context_data(errors=errors)
        return render(self.request, template_name, context)


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
    user_form_class = forms.UserMainForm
    userprofile_form_class = forms.UserProfileMainForm
    page_title = _('Main properties')


class ProfileUpdateView(ProfileTwoFormsView):
    tab = 'update'
    template_name = 'users/profile_update.html'
    user_form_class = forms.UserForm
    userprofile_form_class = forms.UserProfileForm
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
    user_form_class = forms.UserPermissionsForm
    userprofile_form_class = forms.UserProfilePermissionsForm
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
        form = forms.PhotoForm(data=data, files=files, initial={'upload': f})
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
    if not request_user.is_authenticated():
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
            raise PermissionDenied()
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

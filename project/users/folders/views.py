from __future__ import unicode_literals

from collections import namedtuple

from django.contrib import auth, messages
from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext
from django.views import generic

from cauth.mixins import StaffMemberRequiredMixin
from common.pagination.views import IRunnerListView
from common.tree.key import FolderId
from common.tree.mixins import FolderMixin
from storage.utils import create_storage

from users.models import UserFolder, UserProfile
import users.intranetbsu as intranetbsu
import users.intranetbsu.photos as intranetbsuphotos
import users.photo as photo
from users.folders.forms import (
    CreateFolderForm,
    CreateUserForm,
    CreateUsersMassForm,
    IntranetBsuForm,
    UpdateProfileMassForm,
    UploadPhotoMassForm,
)


class UserFolderMixin(FolderMixin):
    root_name = _('Users')
    folder_model = UserFolder
    folder_access_model = None  # TODO

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'folders'
        return context


class CombinedMixin(StaffMemberRequiredMixin, UserFolderMixin):
    pass


class ShowFolderView(CombinedMixin, IRunnerListView):
    template_name = 'users/folder.html'
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        has_users = self.get_queryset().exists()
        can_delete_folder = (not has_users) and (self.node.id is not None) and (len(self.node.children) == 0)

        context['has_users'] = has_users
        context['can_delete_folder'] = can_delete_folder
        return context

    def get_queryset(self):
        return auth.get_user_model().objects.filter(userprofile__folder_id=self.node.id)


class DeleteFolderView(CombinedMixin, generic.base.ContextMixin, generic.View):
    template_name = 'users/folder_confirm_delete.html'
    needs_real_folder = True

    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request):
        folder = self.node.instance
        parent_id = folder.parent_id
        with transaction.atomic():
            # TODO: check that it is empty, ...
            if (folder.get_descendant_count() == 0) and (not folder.userprofile_set.exists()):
                folder.delete()
        return redirect('users:show_folder', FolderId.to_string(parent_id))


class CreateFolderView(CombinedMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = CreateFolderForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_name'] = _('Create folder')
        return context

    def form_valid(self, form):
        UserFolder.objects.create(name=form.cleaned_data['name'], parent_id=self.node.id)
        return redirect('users:show_folder', FolderId.to_string(self.node.id))


class CreateUserView(CombinedMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = CreateUserForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_name'] = _('Create user')
        return context

    def form_valid(self, form):
        with transaction.atomic():
            user = form.save()
            profile = user.userprofile
            profile.folder_id = self.node.id
            profile.save()
        return redirect('users:show_folder', FolderId.to_string(self.node.id))


class CreateUsersMassView(CombinedMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = CreateUsersMassForm
    initial = {'password': '11111'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_name'] = _('Bulk sign-up')
        return context

    def form_valid(self, form):
        pairs = form.cleaned_data['pairs']
        counter = 0
        with transaction.atomic():
            for user, userprofile in pairs:
                user.save()
                userprofile.user = user
                userprofile.folder_id = self.node.id
                userprofile.save()
                counter += 1

        msg = ungettext('%(count)d user was added.', '%(count)d users were added.', counter) % {'count': counter}
        messages.add_message(self.request, messages.INFO, msg)
        return redirect('users:show_folder', FolderId.to_string(self.node.id))


class UpdateProfileMassView(CombinedMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = UpdateProfileMassForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_name'] = _('Bulk profile update')
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['folder_id'] = self.node.id
        return kwargs

    def form_valid(self, form):
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
        return redirect('users:show_folder', FolderId.to_string(self.node.id))


class UploadPhotoMassView(CombinedMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = UploadPhotoMassForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_name'] = _('Bulk photo upload')
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['folder_id'] = self.node.id
        return kwargs

    def form_valid(self, form):
        upload = form.cleaned_data['upload']
        counter = 0
        storage = create_storage()

        with transaction.atomic():
            for user_id, photos in upload.items():
                photo, photo_thumbnail = photos
                photo_id = storage.save(ContentFile(photo))
                photo_thumbnail_id = storage.save(ContentFile(photo_thumbnail))
                counter += UserProfile.objects.filter(pk=user_id).update(photo=photo_id, photo_thumbnail=photo_thumbnail_id)

        msg = ungettext('%(count)d photo has been uploaded.', '%(count)d photos have been uploaded.', counter) % {'count': counter}
        messages.add_message(self.request, messages.INFO, msg)
        return redirect('users:show_folder', FolderId.to_string(self.node.id))


class ObtainPhotosFromIntranetBsuView(CombinedMixin, generic.FormView):
    template_name = 'users/create_form.html'
    form_class = IntranetBsuForm

    UserError = namedtuple('UserError', 'user type message')
    PhotoIds = namedtuple('PhotoIds', 'photo photo_thumbnail')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_name'] = _('Photos from intranet.bsu')
        return context

    def get_initial(self):
        initial = {}
        group = intranetbsu.extract_group(self.node.name)
        if group is not None:
            initial['group'] = group
        return initial

    def form_valid(self, form):
        counter = 0
        photo_ids = {}
        storage = create_storage()

        errors = []
        skip_errors = form.cleaned_data['skip_errors']

        for user in auth.get_user_model().objects.filter(userprofile__folder_id=self.node.id).select_related('userprofile'):
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
                message = getattr(e, 'message', None)
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
            for user_id, ids in photo_ids.items():
                counter += UserProfile.objects.filter(pk=user_id).update(photo=ids.photo, photo_thumbnail=ids.photo_thumbnail)

        msg = ungettext('%(count)d photo has been uploaded.', '%(count)d photos have been uploaded.', counter) % {'count': counter}
        messages.add_message(self.request, messages.INFO, msg)

        if errors:
            return self.error_page(errors)
        else:
            return redirect('users:show_folder', FolderId.to_string(self.node.id))

    def error_page(self, errors):
        template_name = 'users/intranetbsu_errors.html'
        context = self.get_context_data(errors=errors)
        return render(self.request, template_name, context)

from common.cast import make_int_list_quiet
from users.models import UserProfile

from .forms import ShareWithUserForm, ShareWithGroupForm


class BaseShareWithMixin(object):
    access_model = None
    access_model_object_field = None
    _share_form_class = None

    def _get(self, request, obj):
        share_form = self._share_form_class()
        context = {
            'share_form': share_form,
            'acl': self._load_access_control_list(obj),
            'inherited_acl': self._load_inherited_access_control_list(obj),
        }
        return context

    def _post(self, request, obj):
        share_form = self._share_form_class()
        success = False

        if 'grant' in request.POST:
            share_form = self._share_form_class(request.POST)

            if share_form.is_valid():
                self._grant_form_valid(request, obj, share_form)
                success = True

        elif 'revoke' in request.POST:
            access_ids = make_int_list_quiet(request.POST.getlist('id'))
            self.access_model.objects.filter(**{
                self.access_model_object_field: obj
            }).filter(pk__in=access_ids).delete()
            success = True

        context = {
            'share_form': share_form,
            'acl': self._load_access_control_list(obj),
            'inherited_acl': self._load_inherited_access_control_list(obj),
        }
        return success, context

    def _load_access_control_list(self, obj):
        raise NotImplementedError()

    def _load_inherited_access_control_list(self, obj):
        return None

    def _grant_form_valid(self, request, obj, share_form):
        raise NotImplementedError()


class ShareWithUserMixin(BaseShareWithMixin):
    _share_form_class = ShareWithUserForm

    def _load_access_control_list(self, obj):
        return self.access_model.objects.filter(**{
            self.access_model_object_field: obj
        }).order_by('id').all().select_related('who_granted', 'user')

    def _grant_form_valid(self, request, obj, share_form):
        user_id = share_form.cleaned_data['user']
        self.access_model.objects.update_or_create(**{
            self.access_model_object_field: obj,
            'user_id': user_id,
            'defaults': {
                'mode': share_form.cleaned_data['mode'],
                'who_granted': request.user,
            }
        })


class ShareWithGroupMixin(BaseShareWithMixin):
    _share_form_class = ShareWithGroupForm

    def _load_access_control_list(self, obj):
        return self.access_model.objects.filter(**{
            self.access_model_object_field: obj
        }).order_by('id').all().select_related('who_granted', 'group')

    def _grant_form_valid(self, request, obj, share_form):
        group = share_form.cleaned_data['group']
        self.access_model.objects.update_or_create(**{
            self.access_model_object_field: obj,
            'group': group,
            'defaults': {
                'mode': share_form.cleaned_data['mode'],
                'who_granted': request.user,
            }
        })


class ShareFolderWithGroupMixin(ShareWithGroupMixin):
    access_model_object_field = 'folder'

    def _load_inherited_access_control_list(self, obj):
        return self.access_model.objects.filter(**{
            '{}__tree_id'.format(self.access_model_object_field): obj.tree_id,
            '{}__lft__lt'.format(self.access_model_object_field): obj.lft,
            '{}__rght__gt'.format(self.access_model_object_field): obj.rght,
        }).order_by('id').all().select_related(self.access_model_object_field, 'who_granted', 'group')

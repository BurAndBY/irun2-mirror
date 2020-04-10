from common.cast import make_int_list_quiet
from users.models import UserProfile

from .forms import ShareWithUserForm


class ShareWithUserMixin(object):
    access_model = None
    access_model_object_field = None
    userprofile_model_field = None

    def _load_access_control_list(self, obj):
        return self.access_model.objects.filter(**{
            self.access_model_object_field: obj
        }).order_by('id').all()

    def _get(self, request, obj):
        share_form = ShareWithUserForm()
        context = {
            'share_form': share_form,
            'acl': self._load_access_control_list(obj),
        }
        return context

    def _post(self, request, obj):
        share_form = ShareWithUserForm()
        success = False

        if 'grant' in request.POST:
            share_form = ShareWithUserForm(request.POST)

            if share_form.is_valid():
                user_id = share_form.cleaned_data['user']
                self.access_model.objects.update_or_create(**{
                    self.access_model_object_field: obj,
                    'user_id': user_id,
                    'defaults': {
                        'mode': share_form.cleaned_data['mode'],
                        'who_granted': request.user,
                    }
                })
                if self.userprofile_model_field is not None:
                    UserProfile.objects.filter(pk=user_id).update(**{
                        self.userprofile_model_field: True
                    })
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
        }
        return success, context

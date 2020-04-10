from users.models import UserProfile
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def irunner_cauth_show_admin_menu(context):
    request = context['request']

    user = request.user
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True

    profile = UserProfile.objects.\
        filter(pk=user.id).\
        values('has_access_to_problems', 'has_access_to_quizzes', 'has_access_to_admin').\
        first()

    if profile is not None and any(profile.values()):
        return True

    return False


@register.inclusion_tag('cauth/irunner_cauth_share_user.html')
def irunner_cauth_share_user(share_form, acl, can_edit=False):
    return {
        'share_form': share_form,
        'acl': acl,
        'can_edit': can_edit,
    }

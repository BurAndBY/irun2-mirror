from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def irunner_cauth_show_admin_menu(context):
    request = context['request']
    return request.user.is_admin


@register.inclusion_tag('cauth/irunner_cauth_share_user.html')
def irunner_cauth_share_user(share_form, acl, can_edit=False):
    return {
        'share_form': share_form,
        'acl': acl,
        'can_edit': can_edit,
        'user_mode': True,
    }


@register.inclusion_tag('cauth/irunner_cauth_share_user.html')
def irunner_cauth_share_group(share_form, acl, inherited_acl, can_edit=False):
    return {
        'share_form': share_form,
        'acl': acl,
        'inherited_acl': inherited_acl,
        'can_edit': can_edit,
        'user_mode': False,
    }

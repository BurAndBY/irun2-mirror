from django import template
from django.core.urlresolvers import reverse
from django.utils.html import format_html

from users.models import UserProfile

register = template.Library()


@register.inclusion_tag('users/irunner_users_show_tag.html')
def irunner_users_show(user):
    return {'user': user}


@register.simple_tag()
def irunner_users_card(user):
    card_url = reverse('users:card', args=(user.id,))
    user_name = user.get_full_name()

    return format_html(
        u'<a tabindex="0" class="ir-card-link ir-card-link-nohref" role="button" data-poload="{0}">{1}</a>',
        card_url,
        user_name
    )


@register.inclusion_tag('users/irunner_users_list_tag.html')
def irunner_users_list(users, pagination_context=None, show_folder=False, show_checkbox=False):
    return {
        'users': users,
        'pagination_context': pagination_context,
        'show_folder': show_folder,
        'show_checkbox': show_checkbox
    }


@register.inclusion_tag('users/irunner_users_photo_tag.html')
def irunner_users_photo(param):
    user_id = None
    photo = None
    photo_thumbnail = None

    if isinstance(param, UserProfile):
        user_id = param.user_id
        photo = param.photo
        photo_thumbnail = param.photo_thumbnail

    return {
        'enabled': (photo is not None) and (photo_thumbnail is not None),
        'user_id': user_id,
        'photo': photo,
        'photo_thumbnail': photo_thumbnail,
    }

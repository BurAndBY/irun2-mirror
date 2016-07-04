from django import template
from django.core.urlresolvers import reverse
from django.utils.html import format_html

register = template.Library()


@register.inclusion_tag('users/irunner_users_show_tag.html')
def irunner_users_show(user):
    return {'user': user}


@register.simple_tag()
def irunner_users_card(user):
    card_url = reverse('users:card', args=(user.id,))
    user_name = user.get_full_name()

    return format_html(
        u'<a tabindex="0" class="ir-card-link" role="button" data-poload="{0}">{1}</a>',
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

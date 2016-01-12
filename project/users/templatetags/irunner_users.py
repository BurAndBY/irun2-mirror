from django import template

register = template.Library()


@register.inclusion_tag('users/irunner_users_show_tag.html')
def irunner_users_show(user):
    return {'user': user}


@register.inclusion_tag('users/irunner_users_list_tag.html')
def irunner_users_list(users, pagination_context=None, show_folder=False, show_checkbox=False):
    return {
        'users': users,
        'pagination_context': pagination_context,
        'show_folder': show_folder,
        'show_checkbox': show_checkbox
    }

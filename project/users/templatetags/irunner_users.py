from django import template

register = template.Library()


@register.inclusion_tag('users/irunner_users_show_tag.html')
def irunner_users_show(user):
    return {'user': user}

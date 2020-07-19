from django import template
from django.urls import reverse
from django.utils.http import urlquote

register = template.Library()


@register.simple_tag(takes_context=True)
def irunner_next(context):
    '''
    Usage in templates:

        <a href="{% url 'tralala' %}?next={% irunner_next %}">Do</a>

    '''
    request = context['request']
    path = request.GET.get('next')
    if not path:
        path = request.get_full_path()
    if not path:
        path = reverse('home')

    return urlquote(path)

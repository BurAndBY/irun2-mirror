from django import template

register = template.Library()


@register.inclusion_tag('events/irunner_events_logo_tag.html')
def irunner_events_logo(event):
    return {'event': event}

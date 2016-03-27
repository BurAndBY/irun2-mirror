# -*- coding: utf-8 -*-

from django import template

register = template.Library()


@register.inclusion_tag('api/irunner_api_queue_tag.html')
def irunner_api_queue(objects, show_checkboxes=False):
    return {'object_list': objects, 'show_checkboxes': show_checkboxes}

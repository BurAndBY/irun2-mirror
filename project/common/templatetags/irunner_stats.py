from django import template

register = template.Library()


@register.inclusion_tag('common/irunner_stats_proglangbars_tag.html')
def irunner_stats_proglangbars(data):
    return {'data': data}


@register.inclusion_tag('common/irunner_stats_outcomebars_tag.html')
def irunner_stats_outcomebars(data):
    return {'data': data}

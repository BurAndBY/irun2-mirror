from django import template

register = template.Library()


@register.inclusion_tag('home/irunner_home_block_tag.html')
def irunner_home_block(block):
    return {'block': block}

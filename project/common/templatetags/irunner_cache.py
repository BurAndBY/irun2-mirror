from django import template

register = template.Library()


@register.simple_tag
def irunner_cache_lookup(cache, pk):
    return cache.get(pk)

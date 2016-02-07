from django.http import Http404


def str_to_uint(s):
    try:
        n = int(s)
    except (TypeError, ValueError):
        raise Http404('Not an integer')
    if n < 0:
        raise Http404('Less than zero')
    return n

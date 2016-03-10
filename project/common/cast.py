from django.http import Http404


def str_to_uint(s):
    try:
        n = int(s)
    except (TypeError, ValueError):
        raise Http404('Not an integer')
    if n < 0:
        raise Http404('Less than zero')
    return n


def make_int_list_quiet(ids):
    '''
    Fails silently
    '''
    result = set()
    for x in ids:
        for y in x.split(','):
            try:
                y = int(y)
                result.add(y)
            except (TypeError, ValueError):
                pass
    return list(result)

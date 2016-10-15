import json

from functools import wraps

from django.views.decorators.cache import patch_cache_control
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import resolve_url


def get_request_ip(request):
    # TODO: also handle requests passed through proxy
    # x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    # x_forwarded_for.split(',')[-1].strip()

    # if running behind nginx/IIS reverse proxy
    ip = request.META.get('HTTP_X_REAL_IP')
    if ip is not None:
        return ip

    ip = request.META.get('REMOTE_ADDR')
    return ip


def never_ever_cache(decorated_function):
    """Like Django @never_cache but sets more valid cache disabling headers.
    See http://stackoverflow.com/questions/2095520/fighting-client-side-caching-in-django

    @never_cache only sets Cache-Control:max-age=0 which is not
    enough. For example, with max-axe=0 Firefox returns cached results
    of GET calls when it is restarted.
    """
    @wraps(decorated_function)
    def wrapper(*args, **kwargs):
        response = decorated_function(*args, **kwargs)
        patch_cache_control(response, no_cache=True, no_store=True, must_revalidate=True, max_age=0)
        return response
    return wrapper


def redirect_with_query_string(request, *args, **kwargs):
    url = resolve_url(*args, **kwargs)
    if request.GET:
        url += '?'
        url += request.GET.urlencode()
    return HttpResponseRedirect(url)


def make_json_response(data):
    blob = json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8')
    return HttpResponse(blob, content_type='application/json; charset=utf-8')

from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured


class LogRemoteUserMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "LogRemoteUserMiddleware requires AuthenticationMiddleware"
                " to be in MIDDLEWARE before LogRemoteUserMiddleware.")

        response = self.get_response(request)

        # set the header if a user is logged in
        if request.user.is_authenticated():
            response['X-iRunner-Username'] = str(request.user.username)
        return response

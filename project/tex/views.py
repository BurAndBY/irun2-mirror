from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from common.pylightex import tex2html


@method_decorator(csrf_exempt, name='dispatch')
class RenderTeXView(generic.View):
    def post(self, request):
        try:
            tex = request.body.decode('utf-8')
        except UnicodeDecodeError:
            return HttpResponseBadRequest('Invalid encoding')

        html = tex2html(tex)

        return HttpResponse(html)

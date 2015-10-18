from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import StreamingHttpResponse

from .models import AuditRecord
from .forms import TextOrUploadForm
from .storage import create_storage, ResourceId


def _parse_resource(resource_id):
    try:
        return ResourceId.parse(resource_id)
    except:
        raise Http404("Invalid resource id")


# Create your views here.
def new(request):
    form = TextOrUploadForm()
    context = {'form': form}
    return render(request, 'storage/new.html', context)


def upload(request):
    form = TextOrUploadForm(request.POST, request.FILES)

    # check whether it's valid:
    if form.is_valid():
        # process the data in form.cleaned_data as required
        # ...
        # redirect to a new URL:

        upload = form.cleaned_data['upload']

        if upload is not None:
            f = upload
        else:
            text = form.cleaned_data['text']
            f = ContentFile(text.encode('utf-8'))

        storage = create_storage()
        resource_id = storage.save(f)

        event = AuditRecord()
        event.resource_id = resource_id
        event.save()

        url = reverse('storage:show', kwargs={'resource_id': str(resource_id)})
        return HttpResponseRedirect(url)


def show(request, resource_id):
    resource_id = _parse_resource(resource_id)

    storage = create_storage()
    representation = storage.represent(resource_id)

    if representation is None:
        raise Http404("Resource does not exist")

    context = {
        'resource_id': resource_id,
        'representation': representation
    }
    return render(request, 'storage/show.html', context)


def download(request, resource_id):
    resource_id = _parse_resource(resource_id)

    storage = create_storage()
    data = storage.serve(resource_id)

    if data is None:
        raise Http404("Resource does not exist")

    response = StreamingHttpResponse(data.generator, content_type='application/octet-stream')
    response['Content-Length'] = data.size
    return response


def index(request):
    context = {'records': AuditRecord.objects.all()}
    return render(request, 'storage/index.html', context)

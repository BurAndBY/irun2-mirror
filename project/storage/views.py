from django.core.files.base import ContentFile
from django.http import Http404
from django.shortcuts import render, redirect
from django.views import generic

from common.views import StaffMemberRequiredMixin

from utils import serve_resource
from forms import TextOrUploadForm
from storage import create_storage, ResourceId


def _parse_resource(resource_id):
    try:
        return ResourceId.parse(resource_id)
    except:
        raise Http404("Invalid resource id")


class NewView(StaffMemberRequiredMixin, generic.FormView):
    template_name = 'storage/new.html'
    form_class = TextOrUploadForm

    def form_valid(self, form):
        upload = form.cleaned_data['upload']

        if upload is not None:
            f = upload
        else:
            text = form.cleaned_data['text']
            f = ContentFile(text.encode('utf-8'))

        storage = create_storage()
        resource_id = storage.save(f)

        return redirect('storage:show', str(resource_id))


class ShowView(StaffMemberRequiredMixin, generic.View):
    template_name = 'storage/show.html'

    def get(self, request, resource_id):
        resource_id = _parse_resource(resource_id)

        storage = create_storage()
        representation = storage.represent(resource_id)

        if representation is None:
            raise Http404('Resource does not exist')

        context = {
            'resource_id': resource_id,
            'representation': representation
        }
        return render(request, self.template_name, context)


class DownloadView(StaffMemberRequiredMixin, generic.View):
    def get(self, request, resource_id):
        resource_id = _parse_resource(resource_id)
        return serve_resource(request, resource_id, content_type='application/octet-stream', force_download=True)


class IndexView(StaffMemberRequiredMixin, generic.TemplateView):
    template_name = 'storage/index.html'

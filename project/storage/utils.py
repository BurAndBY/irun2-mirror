import mimetypes

from django.http import Http404
from django.http import StreamingHttpResponse
from django.views.decorators.http import etag

from models import FileMetadata
from storage import create_storage, ResourceId


def parse_resource_id(resource_id):
    try:
        return ResourceId.parse(resource_id)
    except:
        raise Http404("Invalid resource id")


def store_with_metadata(f):
    '''
    Saves uploaded file with its name and size (metadata).

    Args:
        f (django.core.files.File): file object (typically uploaded by a user).
    Returns:
        FileMetadata: metadata saved to DB that refers to data saved to file storage.
    '''
    if f is None:
        return None
    storage = create_storage()
    resource_id = storage.save(f)
    return FileMetadata.objects.create(filename=f.name, size=f.size, resource_id=resource_id)


def store_and_fill_metadata(f, filemetadatabase):
    if f is None:
        return
    storage = create_storage()
    resource_id = storage.save(f)
    if f.name is not None:
        filemetadatabase.filename = f.name
    filemetadatabase.size = f.size
    filemetadatabase.resource_id = resource_id


def serve_resource(request, resource_id, content_type=None, force_download=False):
    '''
    Fulfils HTTP GET request serving a file.
    '''
    def do_get_etag(request):
        return str(resource_id)

    @etag(do_get_etag)
    def do_actually_serve(request):
        storage = create_storage()
        data = storage.serve(resource_id)
        if data is None:
            raise Http404()
        response = StreamingHttpResponse(data.generator, content_type=content_type)
        response['Content-Length'] = data.size
        # No cross-browser way to put non-ASCII file name.
        # response['Content-Disposition'] = 'inline; filename="{0}"'.format(filename)
        if force_download:
            response['Content-Disposition'] = 'attachment'
        return response

    return do_actually_serve(request)


def serve_resource_metadata(request, metadata, content_type=None, force_download=False):
    if metadata is None:
        raise Http404()

    if content_type is None:
        # guess MIME type from file extension
        mime_type, _ = mimetypes.guess_type(metadata.filename)
        content_type = mime_type

    return serve_resource(request, metadata.resource_id, content_type=content_type, force_download=force_download)

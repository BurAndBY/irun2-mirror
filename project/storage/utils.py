import mimetypes

from django.http import Http404
from django.http import StreamingHttpResponse

from models import FileMetadata
from storage import create_storage


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


def serve_get(metadata):
    '''
    Fulfils HTTP GET request serving a file.
    '''
    if metadata is None:
        raise Http404()
    mime_type, _ = mimetypes.guess_type(metadata.filename)

    storage = create_storage()
    data = storage.serve(metadata.resource_id)
    if data is None:
        raise Http404()

    response = StreamingHttpResponse(data.generator, content_type=mime_type)
    response['Content-Length'] = data.size

    # No cross-browser way to put non-ASCII file name.
    # response['Content-Disposition'] = 'inline; filename="{0}"'.format(metadata.filename)
    return response

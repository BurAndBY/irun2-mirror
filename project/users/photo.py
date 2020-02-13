import six

from PIL import Image

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

THUMBNAIL_SIZE = (96, 128)


def generate_thumbnail_file(f):
    try:
        im = Image.open(f)
    except IOError:
        raise ValidationError(_('The image cannot be opened and identified.'), code='bad')

    if im.format != 'JPEG':
        raise ValidationError(_('The image format %(format)s is not supported.'), code='format', params={'format': im.format})

    im.thumbnail(THUMBNAIL_SIZE)

    output = six.BytesIO()
    im.save(output, 'JPEG', quality=92)

    return output.getvalue()


def generate_thumbnail_blob(s):
    buff = six.BytesIO()
    buff.write(s)
    buff.seek(0)
    return generate_thumbnail_file(buff)

import re
from collections import namedtuple


class ResourceId(namedtuple('ResourceId', ['hexstr'])):
    def __new__(cls, hexstr):
        if not re.match('^[0-9a-f]*$', hexstr):
            raise ValueError('invalid hex-encoded string: {}'.format(repr(hexstr)))
        return super(ResourceId, cls).__new__(cls, hexstr)


def tojson(resource_id):
    if resource_id is not None:
        if resource_id.hexstr is not None:
            return resource_id.hexstr
    return None

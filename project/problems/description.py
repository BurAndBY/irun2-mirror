import re
from collections import namedtuple

REGEX = re.compile(r'\$\{image:(?P<filename>[\w\.-]+)\}')


class IDescriptionImageLoader(object):
    def get_image_list(self):
        raise NotImplementedError()

RenderResult = namedtuple('RenderResult', 'text images')


def render_description(text, image_loader):
    portions = []
    images = []
    last_start = 0

    all_image_list = None

    for m in REGEX.finditer(text):
        portions.append(text[last_start:m.start()])

        # lazy load to reduce the number of DB queries
        if all_image_list is None:
            all_image_list = image_loader.get_image_list()

        filename = m.group('filename')
        if filename in all_image_list:
            images.append(filename)
        last_start = m.end()

    portions.append(text[last_start:])

    return RenderResult(u''.join(portions), images)

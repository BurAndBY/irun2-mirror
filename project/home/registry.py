from collections import namedtuple


class HomePageBlockStyle(object):
    MY = 0
    COMMON = 1


HomePageBlock = namedtuple('HomePageBlock', [
    'style',
    'icon',
    'name',
    'count',
    'content',
])


class HomePageBlockFactory(object):
    def create_blocks(self, request):
        raise NotImplementedError()

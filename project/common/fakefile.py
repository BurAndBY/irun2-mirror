from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class FakeFile(object):
    def __init__(self, url, name):
        self.url = url
        self.name = name

    def __str__(self):
        return self.name

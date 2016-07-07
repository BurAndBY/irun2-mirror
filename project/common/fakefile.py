class FakeFile(object):
    def __init__(self, url, name):
        self.url = url
        self.name = name

    def __unicode__(self):
        return self.name

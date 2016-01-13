from django.utils.encoding import force_text


class AllObjectsCache(object):
    def __init__(self, model):
        self._data = {}
        for obj in model.objects.all():
            self._data[force_text(obj.pk)] = obj

    def get(self, pk, default=None):
        return self._data.get(force_text(pk), default)

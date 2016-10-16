from django.utils.encoding import force_text


def fetch_objects(model_objects, ids):
    # TODO: split in parts and fetch sequentially if ids is too long
    return {obj.pk: obj for obj in model_objects.filter(pk__in=ids)}


class AllObjectsCache(object):
    def __init__(self, model):
        self._data = {}
        for obj in model.objects.all():
            self._data[force_text(obj.pk)] = obj

    def get(self, pk, default=None):
        return self._data.get(force_text(pk), default)

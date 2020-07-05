from django.utils.encoding import force_text


def fetch_objects(model_objects, ids):
    # TODO: split in parts and fetch sequentially if ids is too long
    return {obj.pk: obj for obj in model_objects.filter(pk__in=ids)}


class AllObjectsCache(object):
    def __init__(self, qs, pks=None):
        self._data = {}

        if pks is not None:
            if len(pks) > 0:
                qs = qs.filter(pk__in=pks)
            else:
                qs = qs.none()

        for obj in qs.order_by():
            self._data[force_text(obj.pk)] = obj

    def get(self, pk, default=None):
        return self._data.get(force_text(pk), default)

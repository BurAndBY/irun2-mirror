from django.utils.encoding import force_text


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

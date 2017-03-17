import six


class EnumMeta(type):
    def iteritems(cls):
        for key, val in six.iteritems(cls.__dict__):
            if key.isupper():
                yield key, val

    def __iter__(cls):
        for key, val in cls.iteritems():
            yield key

    def get(cls, key, default=None):
        try:
            return getattr(cls, key)
        except AttributeError:
            return default

    def __getitem__(cls, key):
        try:
            return getattr(cls, key)
        except AttributeError:
            raise KeyError("Enumerator '{}.{}' does not contain key {!r}".format(cls.__module__, cls.__name__, key))

    def value2key(cls, value):
        for k, v in cls.iteritems():
            if v == value:
                return k
        raise ValueError("Enumerator '{}.{}' does not contain value {!r}".format(cls.__module__, cls.__name__, value))


@six.add_metaclass(EnumMeta)
class Enum(object):
    pass

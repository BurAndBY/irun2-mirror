import random
import string


class IAlgo(object):
    def gen(self):
        raise NotImplementedError()


class DefaultAlgo(IAlgo):
    slug = r'[a-z0-9]{10}'
    length = 10

    def gen(self):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=self.length))


class XkcdAlgo(IAlgo):
    slug = r'xkcd 936'

    def __init__(self):
        from xkcdpass import xkcd_password as xp
        self._xp = xp
        self._wordfile = xp.locate_wordfile()
        self._words = xp.generate_wordlist(wordfile=self._wordfile, min_length=3, max_length=6)

    def gen(self):
        return self._xp.generate_xkcdpassword(self._words, numwords=4, case='capitalize', delimiter='')


def _load_algorithms():
    for kls in [DefaultAlgo, XkcdAlgo]:
        try:
            yield kls()
        except ImportError:
            pass


_ALGORITHMS = list(_load_algorithms())


def get_algo_slugs():
    return [algo.slug for algo in _ALGORITHMS]


def get_algo(slug):
    for algo in _ALGORITHMS:
        if algo.slug == slug:
            return algo
    return _ALGORITHMS[0]

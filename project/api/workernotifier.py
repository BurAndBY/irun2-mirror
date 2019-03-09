from django.conf import settings

from six.moves import urllib


class WorkerNotifier(object):
    '''
    notify() should be called after the transaction has been committed
    '''
    def __init__(self):
        self._workers = set()

    def add_worker(self, worker):
        self._workers.add(worker)

    def notify(self):
        if not settings.SEMAPHORE:
            return

        for worker in self._workers:
            req = urllib.request.Request(settings.SEMAPHORE + 'signal', '')
            if worker.TAG:
                req.add_header('X-iRunner-Worker-Tag', worker.TAG)

            try:
                urllib.request.urlopen(req).read()
            except urllib.error.URLError:
                pass

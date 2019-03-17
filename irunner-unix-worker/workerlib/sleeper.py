import time


class Sleeper:
    def __init__(self, api_client, min_sleep_time):
        self._client = api_client
        self._min_sleep_time = min_sleep_time

    def sleep(self):
        t1 = time.time()
        ok = self._client.wait_on_semaphore()
        if ok:
            return True
        t2 = time.time()

        passed = max(0., t2 - t1)
        if passed < self._min_sleep_time:
            time.sleep(self._min_sleep_time - passed)

        return False

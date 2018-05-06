from functools import wraps

from django.db import OperationalError

MAX_ATTEMPTS = 3


def retry_deadlock(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        attempt = 0
        while True:
            try:
                return func(*args, **kwargs)
            except OperationalError as e:
                if len(e.args) == 0:
                    raise

                code = e.args[0]
                if code != 1213:
                    raise

                # MySQL 'Deadlock found when trying to get lock; try restarting transaction'
                attempt += 1
                if attempt == MAX_ATTEMPTS:
                    raise

    return wrapper

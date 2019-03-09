class Worker(object):
    @classmethod
    def filter_queue(cls, db_obj_qs):
        raise NotImplementedError()

    @classmethod
    def mark(cls, db_obj):
        raise NotImplementedError()


'''
Now workers are determined by 'priority' field:
* priority > 0: default worker
* priority = 0: special UNIX worker

TODO: add a field to DbObjectInQueue model
'''


class DefaultWorker(Worker):
    '''
    UCode.Worker
    '''
    TAG = ''

    @classmethod
    def filter_queue(cls, db_obj_qs):
        return db_obj_qs.filter(priority__gt=0)

    @classmethod
    def mark(cls, db_obj):
        db_obj.priority = max(db_obj.priority, 1)


class UnixWorker(Worker):
    '''
    irunner-unix-worker
    '''
    TAG = 'unix'

    @classmethod
    def filter_queue(cls, db_obj_qs):
        return db_obj_qs.filter(priority=0)

    @classmethod
    def mark(cls, db_obj):
        db_obj.priority = 0


def identify_worker(tag):
    if tag == UnixWorker.TAG:
        return UnixWorker
    return DefaultWorker

from django.utils import timezone
from django.db import transaction

from solutions.models import Judgement

from api.worker import identify_worker
from api.workerchoose import choose_workers
from api.workernotifier import WorkerNotifier
from api.models import DbObjectInQueue
from api.workerstructs import WorkerState
from api.objectinqueue import create_object_in_queue


def enqueue(obj, priority=10):
    '''
    Typical usage:

        with transaction.atomic():
            notifier = enqueue(...)
        # transaction has been committed

        notifier.notify()
    '''
    return bulk_enqueue([obj], priority)


def bulk_enqueue(objs, priority=10):
    '''
    Works as the function above
    '''
    ts = timezone.now()
    notifier = WorkerNotifier()

    db_objs = []
    for obj, worker in choose_workers(objs):
        notifier.add_worker(worker)

        db_obj = DbObjectInQueue(state=DbObjectInQueue.WAITING, creation_time=ts, last_update_time=ts, priority=priority)
        obj.persist(db_obj)
        worker.mark(db_obj)

        db_objs.append(db_obj)

    DbObjectInQueue.objects.bulk_create(db_objs)
    return notifier


def dequeue(worker_name, worker_tag):
    worker = identify_worker(worker_tag)

    while True:
        qs = DbObjectInQueue.objects.\
            order_by('-priority', 'id').\
            filter(state=DbObjectInQueue.WAITING)
        qs = worker.filter_queue(qs)
        db_obj = qs.first()

        if db_obj is None:
            # no jobs
            return None

        with transaction.atomic():
            rows_updated = DbObjectInQueue.objects.\
                filter(pk=db_obj.pk, state=DbObjectInQueue.WAITING).\
                update(state=DbObjectInQueue.EXECUTING, last_update_time=timezone.now(), worker=worker_name)
            rows_updated = 1

            assert rows_updated in (0, 1)
            if rows_updated == 0:
                continue

            db_obj.refresh_from_db()

            obj = create_object_in_queue(db_obj)
            if obj is not None:
                obj.update_state(WorkerState(Judgement.PREPARING))
                return obj
            return None


def finalize(db_obj_id):
    rows_updated = DbObjectInQueue.objects.\
        filter(pk=db_obj_id, state=DbObjectInQueue.EXECUTING).\
        update(state=DbObjectInQueue.DONE, last_update_time=timezone.now())

    assert rows_updated in (0, 1)
    if rows_updated == 1:
        db_obj = DbObjectInQueue.objects.get(pk=db_obj_id)
        return create_object_in_queue(db_obj)


def update(db_obj_id):
    db_obj = DbObjectInQueue.objects.filter(pk=db_obj_id, state=DbObjectInQueue.EXECUTING).first()

    if db_obj is not None:
        return create_object_in_queue(db_obj)

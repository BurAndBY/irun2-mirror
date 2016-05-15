from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from storage.utils import store_with_metadata
from models import MailThread, MailUserThreadVisit


def is_unread(last_viewed_timestamp, last_message_timestamp):
    return last_viewed_timestamp < last_message_timestamp if last_viewed_timestamp is not None else True


def update_last_viewed_timestamp(user, thread, ts):
    MailUserThreadVisit.objects.update_or_create(
        user=user,
        thread=thread,
        defaults={'timestamp': ts}
    )


def _make_mailthread_queryset(course, user, permissions):
    threads = MailThread.objects.filter(course=course)
    if not permissions.messages_all:
        threads = threads.filter(Q(person=user) | Q(person__isnull=True))
    return threads


def list_mail_threads(course, user, permissions):
    '''
    Returns a list of MailThread objects with additional attrs:
        'unread' attr set to true or false,
        'last_viewed_timestamp'.
    '''
    threads = _make_mailthread_queryset(course, user, permissions).\
        select_related('problem').\
        order_by('-last_message_timestamp')

    thread_ids = (thread.id for thread in threads)

    last = {}

    for thread_id, timestamp in MailUserThreadVisit.objects.\
            filter(user=user, thread_id__in=thread_ids).\
            values_list('thread_id', 'timestamp'):
        last[thread_id] = timestamp

    result = []
    for thread in threads:
        last_viewed_timestamp = last.get(thread.id)
        thread.last_viewed_timestamp = last_viewed_timestamp
        thread.unread = is_unread(last_viewed_timestamp, thread.last_message_timestamp)
        result.append(thread)

    return result


def get_unread_thread_count(course, user, permissions):
    if not permissions.messages:
        return None

    threads = _make_mailthread_queryset(course, user, permissions)

    # TODO: less queries
    total_count = threads.count()
    read_count = threads.filter(mailuserthreadvisit__user=user, mailuserthreadvisit__timestamp__gte=F('last_message_timestamp')).count()
    return total_count - read_count


def post_message(user, thread, message_form, is_message_admin):
    ts = timezone.now()

    message = message_form.save(commit=False)

    upload = message_form.cleaned_data['upload']
    if upload is not None:
        message.attachment = store_with_metadata(upload)

    message.author = user
    message.timestamp = ts
    thread.last_message_timestamp = ts
    thread.resolved = is_message_admin

    with transaction.atomic():
        thread.save()
        message.thread = thread
        message.save()
        update_last_viewed_timestamp(user, thread, ts)

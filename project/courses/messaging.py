from collections import namedtuple

from django.db import transaction
from django.db.models import F, Q, Count
from django.utils import timezone

from storage.utils import store_with_metadata
from courses.models import (
    Membership,
    MailThread,
    MailUserThreadVisit,
)


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


MessageCounts = namedtuple('MessageCounts', 'is_my_course unread unresolved')


class MessageCountManager(object):
    '''
    The class is used to display unread message counts on the lists of courses.
    '''

    def __init__(self, user):
        self._user_is_staff = user.is_staff
        self._my_courses = self._fetch_my_courses(user)

        mail_threads = MailThread.objects.all()
        if not self._user_is_staff:  # optimization
            mail_threads = mail_threads.filter(course_id__in=self._my_courses.keys())

        self._all_threads, self._all_read_threads = self._count_threads(mail_threads, user)

        if not self._user_is_staff:  # optimization
            qs = mail_threads.filter(Q(person=user) | Q(person__isnull=True))
            self._my_threads, self._my_read_threads = self._count_threads(qs, user)

        self._mail_threads_unresolved_per_course = self._count_per_course(MailThread.objects.filter(
            resolved=False
        ))

    def _count_threads(self, qs, user):
        return (
            self._count_per_course(qs),
            self._count_per_course(qs.filter(
                mailuserthreadvisit__user=user,
                mailuserthreadvisit__timestamp__gte=F('last_message_timestamp')
            ))
        )

    def _count_per_course(self, qs):
        # {course_id -> count}
        result = {}
        for course_id, count in qs.values_list('course_id').annotate(total=Count('course_id')):
            result[course_id] = count
        return result

    def _fetch_my_courses(self, user):
        # {course_id -> flag 'user can manage all messages'}
        result = {}
        for course_id, role in Membership.objects.filter(user=user).values_list('course_id', 'role'):
            if role == Membership.TEACHER:
                result[course_id] = True
            else:
                result.setdefault(course_id, False)
        return result

    def get(self, course_id):
        is_my_course = self._my_courses.get(course_id)  # False, True or None
        can_manage_messages = self._user_is_staff or is_my_course

        if can_manage_messages:
            return MessageCounts(
                is_my_course is not None,
                self._all_threads.get(course_id, 0) - self._all_read_threads.get(course_id, 0),
                self._mail_threads_unresolved_per_course.get(course_id, 0),
            )
        else:
            return MessageCounts(
                is_my_course is not None,
                self._my_threads.get(course_id, 0) - self._my_read_threads.get(course_id, 0),
                None,
            )

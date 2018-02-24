from collections import namedtuple

from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.translation import ugettext as _

from courses.forms import QueueEntryForm
from courses.models import QueueEntry, QueueEntryStatus
from courses.services import make_student_choices
from courses.views import BaseCourseView, UserCacheMixinMixin


QueueInfo = namedtuple('QueueInfo', 'queue entries can_join can_join_disabled can_manage')
EntryInfo = namedtuple('EntryInfo', 'item is_active is_me can_start can_finish')


class QueueMixin(object):
    tab = 'queue'

    def _is_already_in_queue(self):
        return QueueEntry.objects.filter(queue__course=self.course, user=self.request.user).\
            exclude(status=QueueEntryStatus.DONE).\
            exists()

    def _get_my_subgroup_id(self):
        me = self.get_user_cache().get_user(self.request.user.id)
        if me.subgroup is not None:
            return me.subgroup.id

    def _can_join(self, queue, my_subgroup_id):
        if not queue.is_active:
            return False
        if queue.subgroup_id is not None:
            if queue.subgroup_id != my_subgroup_id:
                return False
        return True


class ListView(QueueMixin, UserCacheMixinMixin, BaseCourseView):
    template_name = 'courses/queue.html'

    def is_allowed(self, permissions):
        return permissions.queue

    def get(self, request, course):
        queue_infos = []
        can_join_disabled = self._is_already_in_queue()
        my_subgroup_id = self._get_my_subgroup_id()

        for queue in course.queue_set.all():
            entries = []
            for entry in queue.queueentry_set.exclude(status=QueueEntryStatus.DONE).order_by('enqueue_time'):
                is_active = entry.status == QueueEntryStatus.IN_PROGRESS
                can_start = self.permissions.queue_admin and (entry.status == QueueEntryStatus.WAITING)
                can_finish = self.permissions.queue_admin and (entry.status == QueueEntryStatus.IN_PROGRESS)
                is_me = entry.user_id == self.request.user.id
                entries.append(EntryInfo(entry, is_active, is_me, can_start, can_finish))

            can_manage = self.permissions.queue_admin
            can_join = (not can_manage) and self._can_join(queue, my_subgroup_id)
            queue_infos.append(QueueInfo(queue, entries, can_join, can_join_disabled, can_manage))

        context = self.get_context_data(queues=queue_infos)
        return render(request, self.template_name, context)


class AddView(QueueMixin, BaseCourseView):
    template_name = 'courses/queue_add.html'

    def is_allowed(self, permissions):
        return permissions.queue_admin

    def _make_form(self, data=None):
        user_cache = self.get_user_cache()
        students = make_student_choices(user_cache)
        form = QueueEntryForm(data=data, user_choices=students, initial={'enqueue_time': timezone.now()})
        return form

    def get(self, request, course, queue_id):
        form = self._make_form()
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course, queue_id):
        form = self._make_form(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.queue_id = queue_id
            item.user_id = form.cleaned_data['user_id']
            item.save()
            return redirect('courses:queues:list', course.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class StartView(QueueMixin, BaseCourseView):
    def is_allowed(self, permissions):
        return permissions.queue_admin

    def post(self, request, course, queue_id, item_id):
        QueueEntry.objects.filter(pk=item_id, queue_id=queue_id, queue__course=course, status=QueueEntryStatus.WAITING).\
            update(status=QueueEntryStatus.IN_PROGRESS, start_time=timezone.now())
        return redirect('courses:queues:list', course.id)


class FinishView(QueueMixin, BaseCourseView):
    def is_allowed(self, permissions):
        return permissions.queue_admin

    def post(self, request, course, queue_id, item_id):
        QueueEntry.objects.filter(pk=item_id, queue_id=queue_id, queue__course=course, status=QueueEntryStatus.IN_PROGRESS).\
            update(status=QueueEntryStatus.DONE, finish_time=timezone.now())
        return redirect('courses:queues:list', course.id)


class JoinView(QueueMixin, BaseCourseView):
    def is_allowed(self, permissions):
        return permissions.queue

    def _do_join(self, request, course, queue_id):
        if self._is_already_in_queue():
            return False
        queue = course.queue_set.filter(pk=queue_id).first()
        if queue is None:
            return False
        if not self._can_join(queue, self._get_my_subgroup_id()):
            return False
        QueueEntry.objects.create(queue_id=queue_id, user=request.user, enqueue_time=timezone.now())
        return True

    def post(self, request, course, queue_id):
        if self._do_join(request, course, queue_id):
            messages.add_message(request, messages.WARNING, _('You have successfully joined the queue.'))
        return redirect('courses:queues:list', course.id)

import re

from courses.models import (
    Activity,
    Course,
    Membership,
    Queue,
    Slot,
    Subgroup,
    Topic,
)
from quizzes.models import QuizInstance


def _next(name):
    m = re.match(r'^(?P<base>.*)\(copy( (?P<num>\d+))?\)$', name)
    if m is not None:
        base = m.group('base')
        num = int(m.group('num')) if m.group('num') is not None else 1
        return '{}(copy {})'.format(base, num + 1)

    if name:
        name += ' '
    name += '(copy)'

    return name


def _lookup(map, pk):
    return map[pk].pk if pk is not None else None


def _copy_course_related(src_course, dst_course, model):
    objects = []
    # need to preserve the order
    for thr in model.objects.filter(course=src_course).order_by('pk'):
        thr.pk = None
        thr.course = dst_course
        objects.append(thr)
    model.objects.bulk_create(objects)


def _copy_topic_related(topics, model):
    objects = model.objects.filter(topic__in=topics)
    for obj in objects:
        obj.pk = None
        obj.topic_id = _lookup(topics, obj.topic_id)
    model.objects.bulk_create(objects)


def clone(src_course, form):
    dst_course = Course.objects.get(pk=src_course.pk)
    dst_course.pk = None
    dst_course.name = _next(src_course.name)
    dst_course.save()

    _copy_course_related(src_course, dst_course, Course.compilers.through)

    enable_subgroups = False
    if form.cleaned_data['copy_subgroups']:
        enable_subgroups = True
        subgroups = Subgroup.objects.filter(course=src_course).in_bulk()
        for subgroup in subgroups.values():
            subgroup.pk = None
            subgroup.course = dst_course
            subgroup.save()

    if form.cleaned_data['copy_users']:
        memberships = []
        for membership in Membership.objects.filter(course=src_course):
            membership.pk = None
            membership.course = dst_course
            membership.subgroup_id = _lookup(subgroups, membership.subgroup_id) if enable_subgroups else None
            memberships.append(membership)
        Membership.objects.bulk_create(memberships)

    if form.cleaned_data['copy_problems']:
        topics = Topic.objects.filter(course=src_course).in_bulk()
        for topic in topics.values():
            topic.pk = None
            topic.course = dst_course
            topic.save()

        _copy_topic_related(topics, Topic.criteria.through)
        _copy_topic_related(topics, Topic.common_problems.through)
        _copy_topic_related(topics, Slot)

        _copy_course_related(src_course, dst_course, Course.common_problems.through)

    enable_quizzes = False
    if form.cleaned_data['copy_quizzes']:
        enable_quizzes = True
        quizzes = QuizInstance.objects.filter(course=src_course).in_bulk()
        for quiz in quizzes.values():
            quiz.pk = None
            quiz.course = dst_course
            quiz.save()

    if form.cleaned_data['copy_queues']:
        queues = []
        for queue in Queue.objects.filter(course=src_course):
            queue.pk = None
            queue.subgroup_id = _lookup(subgroups, queue.subgroup_id) if enable_subgroups else None
            queue.course = dst_course
            queues.append(queue)
        Queue.objects.bulk_create(queues)

    if form.cleaned_data['copy_sheet']:
        activities = []
        for activity in Activity.objects.filter(course=src_course):
            activity.pk = None
            activity.course = dst_course
            activity.quiz_instance_id = _lookup(quizzes, activity.quiz_instance_id) if enable_quizzes else None
            activities.append(activity)
        Activity.objects.bulk_create(activities)

    return dst_course.pk

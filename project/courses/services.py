# -*- coding: utf-8 -*-

from django.contrib import auth
from django.db.models import F
from django.utils.encoding import force_text

from itertools import chain
from collections import namedtuple

from common.constants import EMPTY_SELECT
from problems.models import Problem
from solutions.models import Solution, Judgement


from models import Assignment, Criterion, Membership, Activity, ActivityRecord, AssignmentCriteriaIntermediate

'''
Cache of Course Users
'''


class UserDescription(namedtuple('UserDescription', 'id first_name last_name subgroup_name')):
    def __unicode__(self):
        '''
        Returns a string in the form of 'name surname (subgroup)'.
        '''
        if self.subgroup_name:
            return u'{0} {1} ({2})'.format(self.first_name, self.last_name, self.subgroup_name)
        else:
            return u'{0} {1}'.format(self.first_name, self.last_name)


class UserCache(object):
    def __init__(self, course_id):
        self._user_descriptions = {}
        self._teachers = []
        self._students = []

        for membership in Membership.objects.\
                filter(course_id=course_id).\
                select_related('user', 'subgroup').\
                order_by('user__last_name', 'user__first_name', 'user__id'):
            user = membership.user
            subgroup_name = membership.subgroup.name if membership.subgroup else None
            descr = UserDescription(user.id, user.first_name, user.last_name, subgroup_name)
            self._put(user.id, descr)

            if membership.role == Membership.STUDENT:
                self._students.append(descr)
            elif membership.role == Membership.TEACHER:
                self._teachers.append(descr)

    def _put(self, user_id, descr):
        self._user_descriptions[force_text(user_id)] = descr
        return descr

    def _fallback(self, user_id):
        '''
        E. g. the user has been removed from the course.
        '''
        User = auth.get_user_model()
        user = User.objects.get(pk=user_id)
        return UserDescription(user.id, user.first_name, user.last_name, None)

    def list_students(self):
        return self._students

    def get_user(self, user_id):
        '''
        Returns UserDescription instance.
        '''
        descr = self._user_descriptions.get(force_text(user_id))
        if descr is None:
            descr = self._fallback(user_id)
            self._put(user_id, descr)
        return descr


'''
Helpers to build <select> field with a list of problems.
'''


class ProblemChoicesBuilder(object):
    '''
    Helper to build dynamic choices for TypedChoiceField
    '''
    def __init__(self, topics):
        self._topics = topics
        self._folder_problems = {}

    def add(self, folder_id, problem):
        self._folder_problems.setdefault(folder_id, []).append(problem)

    def get(self, empty_select):
        data = []
        if empty_select is not None:
            data.append((None, empty_select))

        for topic in self._topics:
            problems = self._folder_problems.get(topic.problem_folder_id)
            if problems is None:
                continue

            group = tuple((problem.id, problem.numbered_full_name()) for problem in problems)
            data.append((topic.name, group))

        return tuple(data)


def make_problem_choices(course, full=False, user_id=None, membership_id=None, empty_select=EMPTY_SELECT):
    topics = course.topic_set.all()
    builder = ProblemChoicesBuilder(topics)

    if full:
        folder_ids = set(topic.problem_folder_id for topic in topics)
        for problem in Problem.objects.filter(folders__id__in=folder_ids).annotate(folder_id=F('folders__id')):
            builder.add(problem.folder_id, problem)

    if user_id is not None:
        for problem in Problem.objects.\
                filter(assignment__membership__user_id=user_id).\
                annotate(folder_id=F('assignment__topic__problem_folder_id')).\
                order_by('assignment__topic_id', 'assignment__slot_id', 'id'):
            builder.add(problem.folder_id, problem)

    if membership_id is not None:
        for problem in Problem.objects.filter(assignment__membership_id=membership_id).annotate(folder_id=F('assignment__topic__problem_folder_id')):
            builder.add(problem.folder_id, problem)

    return builder.get(empty_select)


def make_student_choices(user_cache, empty_select=EMPTY_SELECT):
    data = [(None, empty_select)]
    for user_descr in user_cache.list_students():
        data.append((unicode(user_descr.id), unicode(user_descr)))
    return tuple(data)


'''
Cousre results calculation

descr means description
'''

CourseResults = namedtuple('CourseResults', 'course_descr user_results')


def make_course_results(course):
    '''
    main function
    '''
    course_descr = CourseDescr(course)

    # fetch all students from the course in conventional order
    memberships = Membership.objects.\
        filter(course_id=course.id, role=Membership.STUDENT).\
        select_related('user', 'subgroup').\
        order_by('user__last_name', 'user__first_name', 'user__id')

    results = []
    # indexes for fast lookup to results array items
    user_id_result = {}
    membership_id_result = {}

    for membership in memberships:
        user = membership.user
        result = UserResult(course_descr, user, membership)
        results.append(result)

        user_id_result[user.id] = result
        membership_id_result[membership.id] = result

    # assignment criteria
    assignment_criterion_ids = {}
    for ac in AssignmentCriteriaIntermediate.objects.filter(assignment__membership__course=course):
        assignment_criterion_ids.setdefault(ac.assignment_id, []).append(ac.criterion_id)

    # assignments
    for assignment in Assignment.objects.\
            filter(membership__course=course, membership__role=Membership.STUDENT).\
            select_related('problem'):
        mid = assignment.membership_id
        criterion_ids = assignment_criterion_ids.get(assignment.id, [])
        membership_id_result[mid].register_assignment(assignment, criterion_ids)

    # activity records
    for record in ActivityRecord.objects.\
            filter(membership__course=course, membership__role=Membership.STUDENT):
        mid = record.membership_id
        membership_id_result[mid].register_activity_record(record)

    # solutions
    for solution in Solution.objects.\
            filter(coursesolution__course=course).\
            select_related('best_judgement'):
        user_result = user_id_result.get(solution.author_id)
        if user_result is not None:
            user_result.register_solution(solution)

    return CourseResults(course_descr, results)


def make_course_single_result(course, membership, user=None):
    '''
    Works like above, but returns results only for one student.
    '''
    assert membership.course_id == course.id
    assert membership.role == Membership.STUDENT

    if user is not None:
        # save one SQL query
        assert membership.user_id == user.id
    else:
        user = membership.user

    course_descr = CourseDescr(course)
    result = UserResult(course_descr, user, membership)

    # assignment criteria
    assignment_criterion_ids = {}
    for ac in AssignmentCriteriaIntermediate.objects.filter(assignment__membership=membership):
        assignment_criterion_ids.setdefault(ac.assignment_id, []).append(ac.criterion_id)

    # assignments
    for assignment in Assignment.objects.filter(membership=membership).\
            select_related('problem'):
        criterion_ids = assignment_criterion_ids.get(assignment.id, [])
        result.register_assignment(assignment, criterion_ids)

    # activity records
    for record in ActivityRecord.objects.filter(membership=membership):
        result.register_activity_record(record)

    # solutions
    for solution in Solution.objects.filter(coursesolution__course=course, author_id=membership.user_id).\
            select_related('best_judgement'):
        result.register_solution(solution)

    return result


class CourseDescr(object):
    def __init__(self, course):
        self.topic_descrs = []
        self._topic_id_to_index = {}

        for topic in course.topic_set.prefetch_related('criteria').prefetch_related('slot_set').all():
            descr = TopicDescr(topic)
            self._topic_id_to_index[topic.id] = len(self.topic_descrs)
            self.topic_descrs.append(descr)

        self.activities = []
        self._activity_id_to_index = {}
        for activity in course.activity_set.all():
            self._activity_id_to_index[activity.id] = len(self.activities)
            self.activities.append(activity)

        self.subgroups = list(course.subgroup_set.order_by('id'))

    def get_topic_index(self, topic_id):
        return self._topic_id_to_index[topic_id]

    def get_activity_index(self, activity_id):
        return self._activity_id_to_index[activity_id]

    def get_main_activities(self):
        return [activity for activity in self.activities if activity.weight > 0.0]

    def get_extra_activities(self):
        return [activity for activity in self.activities if activity.weight == 0.0]


class TopicDescr(object):
    def __init__(self, topic):
        self.topic = topic
        self.criteria = list(topic.criteria.all())

        self.slots = []
        self._id_to_index = {}

        for slot in topic.slot_set.all():
            self._id_to_index[slot.id] = len(self.slots)
            self.slots.append(slot)

    def get_slot_count(self):
        return len(self.slots)

    def get_slot_index(self, slot_id):
        return self._id_to_index[slot_id]


class CriterionDescr(object):
    def __init__(self, criterion):
        self.criterion = criterion
        self.ok = False


def _choose_better_solution(s1, s2):
    j1, j2 = s1.best_judgement, s2.best_judgement
    # diff = (j2.score / j2.max_score) - (j1.score / j1.max_score)
    diff_sign = j2.score * j1.max_score - j2.max_score * j1.score

    if diff_sign < 0:
        return s1
    elif diff_sign > 0:
        return s2
    else:
        return (s2 if (s1.reception_time <= s2.reception_time) else s1)


class ProblemResult(object):
    def __init__(self, problem):
        assert problem is not None
        self.problem = problem
        self.best_solution = None
        self.attempts = 0
        self.max_attempts = None
        self.solutions = []

    def register_solution(self, solution):
        if self.problem.id != solution.problem_id:
            return

        self.attempts += 1
        self.solutions.append(solution)
        judgement = solution.best_judgement

        if judgement is None:
            return
        if judgement.status != Judgement.DONE:
            return

        if self.best_solution is None:
            self.best_solution = solution
        else:
            self.best_solution = _choose_better_solution(self.best_solution, solution)

    def was_submitted(self):
        return self.best_solution is not None

    def get_score(self):
        return self.best_solution.best_judgement.score

    def get_max_score(self):
        return self.best_solution.best_judgement.max_score

    def is_ok(self):
        return self.best_solution.best_judgement.score == self.best_solution.best_judgement.max_score


class SlotResult(object):
    def __init__(self, topic_descr, slot=None):
        self.topic_descr = topic_descr
        self.slot = slot
        self.assignment = None
        self.problem_result = None
        self.criterion_descrs = [CriterionDescr(criterion) for criterion in topic_descr.criteria]

    def register_assignment(self, assignment, criterion_ids):
        assert self.assignment is None, 'duplicate problem assignment for the same slot'
        self.assignment = assignment
        # do not touch assignment.criteria because it spawns a DB query!
        for criterion_id in criterion_ids:
            self._set_criterion(criterion_id)

        if assignment.problem is not None:
            self.problem_result = ProblemResult(assignment.problem)

    def register_solution(self, solution):
        if self.problem_result is not None:
            self.problem_result.register_solution(solution)

    def is_penalty(self):
        return self.slot is None

    def _set_criterion(self, criterion_id):
        for criterion_descr in self.criterion_descrs:
            if criterion_descr.criterion.id == criterion_id:
                criterion_descr.ok = True
                return
        # We can get here if some criteria were checked for students and then removed from the course.
        # assert False, 'unknown criterion'

    def should_show_in_standings(self):
        return self.problem_result is not None


class TopicResult(object):
    def __init__(self, topic_descr):
        self.topic_id = topic_descr.topic.id
        self.topic_descr = topic_descr
        self.slot_results = [SlotResult(topic_descr, slot) for slot in topic_descr.slots]
        self.penalty_problem_results = []

    def get_slot_and_penalty_results(self):
        return self.slot_results + self.penalty_problem_results

    def register_assignment(self, assignment, criterion_ids):
        if assignment.slot_id is not None:
            idx = self.topic_descr.get_slot_index(assignment.slot_id)
            self.slot_results[idx].register_assignment(assignment, criterion_ids)
        else:
            slot_result = SlotResult(self.topic_descr)
            slot_result.register_assignment(assignment, criterion_ids)
            self.penalty_problem_results.append(slot_result)

    def register_solution(self, solution):
        for slot_result in self.slot_results:
            slot_result.register_solution(solution)
        for slot_result in self.penalty_problem_results:
            slot_result.register_solution(solution)


class ActivityResult(object):
    def __init__(self, activity):
        self.activity = activity
        self.record = None

    def register_activity_record(self, record):
        assert self.record is None, 'two activity records'
        self.record = record

    def get_html_class(self):
        if self.activity.kind == Activity.MARK:
            return 'ir-sheet-editable ir-sheet-editable-mark'
        elif self.activity.kind == Activity.PASSED_OR_NOT:
            return 'ir-sheet-editable ir-sheet-editable-enum'
        else:
            return 'ir-sheet-readonly'

    def get_html_contents(self):
        if self.activity.kind == Activity.PROBLEM_SOLVING:
            return u''  # TODO
        if self.record is not None:
            if self.activity.kind == Activity.MARK:
                if self.record.mark > 0:
                    return unicode(self.record.mark)
            elif self.activity.kind == Activity.PASSED_OR_NOT:
                return self.record.get_enum_display()

        return u''


class UserResult(object):
    def __init__(self, course_descr, user, membership):
        self.course_descr = course_descr
        self.user = user
        self.membership = membership
        self.topic_results = [TopicResult(topic_descr) for topic_descr in course_descr.topic_descrs]
        self.activity_results = [ActivityResult(activity) for activity in course_descr.activities]

    def get_slot_results(self):
        for topic_result in self.topic_results:
            for slot_result in topic_result.slot_results:
                yield slot_result

    def get_main_activity_results(self):
        return [res for res in self.activity_results if res.activity.weight > 0.0]

    def get_extra_activity_results(self):
        return [res for res in self.activity_results if res.activity.weight == 0.0]

    def get_subgroup_class_suffix(self):
        '''
        Returns empty string if user does not belong to subgroup.
        Returns '1', '2', ... if he does.
        '''
        subgroup = self.membership.subgroup
        try:
            idx = self.course_descr.subgroups.index(subgroup)
        except ValueError:
            return u''

        return unicode(idx + 1)

    def register_assignment(self, assignment, criterion_ids):
        if assignment.topic_id is not None:
            idx = self.course_descr.get_topic_index(assignment.topic_id)
            self.topic_results[idx].register_assignment(assignment, criterion_ids)
        else:
            # TODO: this is extra problem
            pass

    def register_solution(self, solution):
        for topic_result in self.topic_results:
            topic_result.register_solution(solution)
        # TODO: extra problems

    def register_activity_record(self, record):
        idx = self.course_descr.get_activity_index(record.activity_id)
        self.activity_results[idx].register_activity_record(record)

    def get_slot_result(self, assignment):
        for topic_result in self.topic_results:
            for slot_result in chain(topic_result.slot_results, topic_result.penalty_problem_results):
                if slot_result.assignment == assignment:
                    return slot_result

        raise ValueError('no slot result was found for assignment')

# -*- coding: utf-8 -*-

from collections import namedtuple

from common.constants import EMPTY_SELECT
from problems.models import Problem
from solutions.models import Solution, Judgement


from models import Assignment, Membership, Activity, ActivityRecord

'''
Helpers to build <select> field with a list of problems.
'''


class ProblemChoicesBuilder(object):
    '''
    Helper to build dynamic choices for TypedChoiceField
    '''
    def __init__(self):
        self._data = [(None, EMPTY_SELECT)]

    def add(self, name, problems):
        group = tuple((problem.id, problem.numbered_full_name()) for problem in problems)
        if group:
            self._data.append((name, group))

    def get(self):
        return tuple(self._data)


def make_problem_choices(course, full=False, user_id=None, membership_id=None):
    builder = ProblemChoicesBuilder()
    topics = course.topic_set.all()

    def reorder(qs):
        return qs.order_by('number', 'subnumber', 'full_name')

    if full:
        for topic in topics:
            if topic.problem_folder is not None:
                builder.add(topic.name, reorder(topic.problem_folder.problem_set.all()))

    if user_id is not None:
        for topic in topics:
            problems = Problem.objects.filter(assignment__topic=topic, assignment__membership__user_id=user_id)
            builder.add(topic.name, reorder(problems))

    if membership_id is not None:
        for topic in topics:
            problems = Problem.objects.filter(assignment__topic=topic, assignment__membership_id=membership_id)
            builder.add(topic.name, reorder(problems))

    return builder.get()

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
    memberships = course.get_student_memberships()

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

    # assignments
    for assignment in Assignment.objects.filter(membership__course=course, membership__role=Membership.STUDENT).prefetch_related('criteria'):
        mid = assignment.membership_id
        membership_id_result[mid].register_assignment(assignment)

    # activity records
    for record in ActivityRecord.objects.filter(membership__course=course, membership__role=Membership.STUDENT):
        mid = record.membership_id
        membership_id_result[mid].register_activity_record(record)

    # solutions
    for solution in Solution.objects.filter(coursesolution__course=course).select_related('best_judgement'):
        user_result = user_id_result.get(solution.author.id)
        if user_result is not None:
            user_result.register_solution(solution)

    return CourseResults(course_descr, results)


def make_course_single_result(course, membership):
    '''
    Works like above, but returns results only for one student.
    '''
    assert membership.course == course
    assert membership.role == Membership.STUDENT

    course_descr = CourseDescr(course)
    result = UserResult(course_descr, membership.user, membership)

    # assignments
    for assignment in Assignment.objects.filter(membership=membership).prefetch_related('criteria'):
        result.register_assignment(assignment)

    # activity records
    for record in ActivityRecord.objects.filter(membership=membership):
        result.register_activity_record(record)

    # TODO: solutions

    return result


class CourseDescr(object):
    def __init__(self, course):
        self.topic_descrs = []
        self._topic_id_to_index = {}

        for topic in course.topic_set.all():
            descr = TopicDescr(topic)
            self._topic_id_to_index[topic.id] = len(self.topic_descrs)
            self.topic_descrs.append(descr)

        self.activities = []
        self._activity_id_to_index = {}
        for activity in course.activity_set.all():
            self._activity_id_to_index[activity.id] = len(self.activities)
            self.activities.append(activity)

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

    def register_solution(self, solution):
        if self.problem != solution.problem:
            return

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
        self.slot = slot
        self.assignment = None
        self.problem_result = None
        self.criterion_descrs = [CriterionDescr(criterion) for criterion in topic_descr.criteria]

    def register_assignment(self, assignment):
        assert self.assignment is None, 'duplicate problem assignment for the same slot'
        self.assignment = assignment
        for criterion in assignment.criteria.all():
            self._set_criterion(criterion)

        if assignment.problem is not None:
            self.problem_result = ProblemResult(assignment.problem)

    def register_solution(self, solution):
        if self.problem_result is not None:
            self.problem_result.register_solution(solution)

    def is_penalty(self):
        return self.slot is None

    def _set_criterion(self, criterion):
        for criterion_descr in self.criterion_descrs:
            if criterion_descr.criterion.id == criterion.id:
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

    def register_assignment(self, assignment):
        if assignment.slot_id is not None:
            idx = self.topic_descr.get_slot_index(assignment.slot_id)
            self.slot_results[idx].register_assignment(assignment)
        else:
            slot_result = SlotResult(self.topic_descr)
            slot_result.register_assignment(assignment)
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

    def register_assignment(self, assignment):
        if assignment.topic_id is not None:
            idx = self.course_descr.get_topic_index(assignment.topic_id)
            self.topic_results[idx].register_assignment(assignment)
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

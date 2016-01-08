from collections import namedtuple


class ProblemResult(object):
    def __init__(self, points, max_points):
        self.points = points
        self.max_points = max_points

    def is_full_solution(self):
        return self.points == self.max_points


class CourseResultsManager(object):
    def __init__(self, course):
        pass

    def get(self, user_id, problem_id):
        return None

'''
descr means description
'''


class CourseDescr(object):
    def __init__(self, course):
        self.topic_descrs = []
        self._id_to_index = {}

        for topic in course.topic_set.all():
            descr = TopicDescr(topic)
            self._id_to_index[topic.id] = len(self.topic_descrs)
            self.topic_descrs.append(descr)

    def get_topic_index(self, topic_id):
        return self._id_to_index[topic_id]


class TopicDescr(object):
    def __init__(self, topic):
        self.topic = topic

        self.slots = []
        self._id_to_index = {}

        for slot in topic.slot_set.all():
            self._id_to_index[slot.id] = len(self.slots)
            self.slots.append(slot)

    def get_slot_count(self):
        return len(self.slots)

    def get_slot_index(self, slot_id):
        return self._id_to_index[slot_id]


class SlotResult(object):
    def __init__(self, slot=None):
        self.slot = slot
        self.assignment = None

    def register_assignment(self, assignment):
        assert self.assignment is None, 'duplicate problem assignment for the same slot'
        self.assignment = assignment

    def should_show_in_standings(self):
        return self.assignment is not None and self.assignment.problem is not None


class TopicResult(object):
    def __init__(self, topic_descr):
        self.topic_id = topic_descr.topic.id
        self.topic_descr = topic_descr
        self.slot_results = [SlotResult(slot) for slot in topic_descr.slots]
        self.penalty_problem_results = []

    def register_assignment(self, assignment):
        if assignment.slot_id is not None:
            idx = self.topic_descr.get_slot_index(assignment.slot_id)
            self.slot_results[idx].register_assignment(assignment)
        else:
            slot_result = SlotResult()
            slot_result.register_assignment(assignment)
            self.penalty_problem_results.append(slot_result)


class UserResult(object):
    def __init__(self, course_descr, user, membership):
        self.course_descr = course_descr
        self.user = user
        self.membership = membership
        self.topic_results = [TopicResult(topic_descr) for topic_descr in course_descr.topic_descrs]

    def get_slot_results(self):
        for topic_result in self.topic_results:
            for slot_result in topic_result.slot_results:
                yield slot_result

    def register_assignment(self, assignment):
        if assignment.topic_id is not None:
            idx = self.course_descr.get_topic_index(assignment.topic_id)
            self.topic_results[idx].register_assignment(assignment)
        else:
            # TODO: this is extra problem
            pass

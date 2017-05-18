from __future__ import unicode_literals

from django.utils.encoding import smart_text

from .models import Activity, ActivityRecord


class ActivityResult(object):
    record = None

    def __init__(self, activity):
        self.activity = activity

    def register_activity_record(self, record):
        if self.record is not None:
            raise ValueError('two activity records')
        self.record = record

    def get_html_class(self):
        return ' '.join(self.get_html_classes())

    # methods to override

    def get_html_classes(self):
        '''
        Returns CSS class of <td>...</td>
        '''
        return []

    def get_html_contents(self):
        '''
        Returns contents of <td>...</td>
        '''
        return ''

    def get_mark(self):
        '''
        Returns 10-point grade
        '''
        return 0


class ProblemSolvingResult(ActivityResult):
    def __init__(self, activity, problem_solving_mark):
        super(ProblemSolvingResult, self).__init__(activity)
        self.problem_solving_mark = problem_solving_mark

    def get_html_classes(self):
        return ['ir-score']

    def get_html_contents(self):
        return smart_text(self.problem_solving_mark.get_mark())

    def get_mark(self):
        return self.problem_solving_mark.get_mark()


class MarkResult(ActivityResult):
    def get_html_classes(self):
        classes = ['ir-sheet-editable', 'ir-score', 'ir-sheet-editable-mark']
        if self.record is not None and self.record.mark in (1, 2, 3):
            classes.append('ir-sheet-bad')
        return classes

    def get_html_contents(self):
        if self.record is not None:
            if self.record.mark > 0:
                return smart_text(self.record.mark)
        return ''

    def get_mark(self):
        if self.record is not None:
            return self.record.mark
        return 0


class PassedOrNotResult(ActivityResult):
    def get_html_classes(self):
        classes = ['ir-sheet-editable', 'ir-sheet-editable-enum']
        if self.record is not None and self.record.enum in (ActivityRecord.NO_PASS, ActivityRecord.ABSENCE):
            classes.append('ir-sheet-bad')
        return classes

    def get_html_contents(self):
        if self.record is not None:
            return self.record.get_enum_display()
        return ''

    def get_mark(self):
        if self.record is not None:
            return 10 if (self.record.enum == ActivityRecord.PASS) else 0
        return 0


class QuizResult(ActivityResult):
    def __init__(self, activity, quiz_results):
        super(QuizResult, self).__init__(activity)
        self.quiz_results = quiz_results

    def _mark(self):
        mark = self.quiz_results.get(self.activity.quiz_instance_id)
        if mark is not None:
            mark = int(mark)
        return mark

    def get_html_classes(self):
        classes = ['ir-score']
        mark = self._mark()
        if mark is not None and mark < 4:
            classes.append('ir-sheet-bad')
        return classes

    def get_html_contents(self):
        mark = self._mark()
        if mark is not None:
            return smart_text(mark)
        return ''

    def get_mark(self):
        mark = self._mark()
        return mark if mark is not None else 0


def make_activity_result(activity, problem_solving_mark, quiz_results):
    kind = activity.kind

    if kind == Activity.MARK:
        return MarkResult(activity)
    if kind == Activity.PASSED_OR_NOT:
        return PassedOrNotResult(activity)
    if kind == Activity.PROBLEM_SOLVING:
        return ProblemSolvingResult(activity, problem_solving_mark)
    if kind == Activity.QUIZ_RESULT:
        return QuizResult(activity, quiz_results)

    return ActivityResult()

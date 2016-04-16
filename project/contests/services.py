# -*- coding: utf-8 -*-

from collections import namedtuple

from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from common.constants import EMPTY_SELECT, make_empty_select
from common.outcome import Outcome
from problems.models import Problem
from solutions.models import Judgement

from .models import ContestSolution, Membership

LabeledProblem = namedtuple('LabeledProblem', 'letter problem')

LETTERS = u'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def make_letter(x):
    result = []
    while True:
        result.append(LETTERS[x % len(LETTERS)])
        x //= len(LETTERS)
        if x == 0:
            break
    return u''.join(reversed(result))


def make_lettered_name(letter, name):
    if name:
        return u'{0}: {1}'.format(letter, name)
    else:
        return letter


def make_problem_choices(contest):
    result = []
    result.append((None, make_empty_select(_('Problem'))))
    for i, problem in enumerate(contest.get_problems()):
        text = make_lettered_name(make_letter(i), problem.unnumbered_brief_name())
        result.append((problem.id, text))
    return tuple(result)


def make_contestant_choices(contest, empty_label=None):
    result = []
    if empty_label is None:
        empty_label = make_empty_select(_('Contestant'))
    result.append((None, empty_label))
    for user in contest.members.filter(contestmembership__role=Membership.CONTESTANT):
        result.append((user.id, user.get_full_name()))
    return tuple(result)


class ProblemResolver(object):
    def __init__(self, contest):
        self._problems = {}
        for i, problem in enumerate(contest.get_problems()):
            self._problems[force_text(problem.id)] = make_lettered_name(make_letter(i), problem.short_name)

    def get_problem_name(self, problem_id):
        name = self._problems.get(force_text(problem_id))
        if name is None:
            # fallback
            problem = Problem.objects.filter(pk=problem_id).first()
            if problem is not None:
                name = problem.unnumbered_brief_name()
            else:
                name = EMPTY_SELECT
        return name


class ContestTiming(object):
    '''
    This class knows nothing about permissions and access rights.
    It is responsible for time only.
    '''
    BEFORE = 0
    IN_PROGRESS = 1
    AFTER = 2

    def get(self):
        return self._status

    def is_freeze_applicable(self):
        return self._freeze_applicable

    def get_time_passed(self):
        return self._time_passed

    def get_time_total(self):
        return self._time_total

    def get_time_before(self):
        return self._time_before

    def __init__(self, contest):
        ts = timezone.now().replace(microsecond=0)

        self._time_passed = None
        self._time_total = contest.duration
        self._time_before = None

        if ts < contest.start_time:
            self._status = ContestTiming.BEFORE
            self._time_before = contest.start_time - ts

        elif ts < contest.start_time + contest.duration:
            self._status = ContestTiming.IN_PROGRESS
            self._time_passed = ts - contest.start_time

        else:
            self._status = ContestTiming.AFTER
            self._time_passed = contest.duration

        self._freeze_applicable = False
        if contest.freeze_time is not None:
            if self._status == ContestTiming.IN_PROGRESS:
                if ts >= contest.start_time + contest.freeze_time:
                    self._freeze_applicable = True
            elif self._status == ContestTiming.AFTER:
                if not contest.unfreeze_standings:
                    self._freeze_applicable = True


RunDescription = namedtuple('RunDescription', 'user labeled_problem when')
ContestResults = namedtuple('ContestResults', 'contest contest_descr frozen user_results last_success last_run')


def _get_kind(cs, freeze_time, show_pending_runs):
    if (freeze_time is not None) and (cs.solution.reception_time >= freeze_time):
        return SolutionKind.PENDING if show_pending_runs else None

    judgement = cs.fixed_judgement if cs.fixed_judgement is not None else cs.solution.best_judgement

    if judgement is not None and judgement.status == Judgement.DONE:
        if judgement.outcome == Outcome.COMPILATION_ERROR:
            # skip CE
            return None
        if judgement.outcome == Outcome.ACCEPTED:
            return SolutionKind.ACCEPTED
        elif judgement.outcome == Outcome.CHECK_FAILED:
            return SolutionKind.PENDING
        else:
            return SolutionKind.REJECTED
    else:
        return SolutionKind.PENDING


def make_contest_results(contest, frozen):
    contest_descr = ContestDescr(contest)

    # fetch all contestants from the contest
    users = contest.members.filter(contestmembership__role=Membership.CONTESTANT)
    user_id_result = {}
    for user in users:
        user_id_result[user.id] = UserResult(contest_descr, user)

    # fetch solutions
    queryset = ContestSolution.objects.\
        filter(contest=contest).\
        filter(solution__reception_time__gte=contest.start_time, solution__reception_time__lt=contest.start_time+contest.duration).\
        select_related('fixed_judgement', 'solution', 'solution__best_judgement').\
        order_by('solution__reception_time')

    freeze_time = None
    if frozen and (contest.freeze_time is not None):
        freeze_time = contest.start_time + contest.freeze_time

    last_success = None
    last_run = None

    for cs in queryset:
        user_result = user_id_result.get(cs.solution.author_id)
        if user_result is None:
            # The user is a juror or a contestant that has been excluded from the contest.
            continue

        problem_index = contest_descr.get_problem_index(cs.solution.problem_id)
        if problem_index is None:
            # The problem has been excluded from th contest.
            continue

        kind = _get_kind(cs, freeze_time, contest.show_pending_runs)
        if kind is None:
            continue

        when = cs.solution.reception_time - contest.start_time
        penalty_time = when.seconds // 60
        user_result.register_solution(problem_index, kind, penalty_time)

        run = RunDescription(user_result.user, contest_descr.labeled_problems[problem_index], when)
        last_run = run
        if kind == SolutionKind.ACCEPTED:
            last_success = run

    user_results = user_id_result.values()
    for user_result in user_results:
        user_result.finalize()

    # order the table
    user_results.sort(key=lambda x: x.get_key())

    # put places
    place = 0
    tag = 0
    for i, user_result in enumerate(user_results):
        if (i == 0) or (user_results[i - 1].get_key() != user_results[i].get_key()):
            place = i
        if (i > 0) and (user_results[i - 1].get_solved_problem_count() != user_results[i].get_solved_problem_count()):
            tag = tag ^ 1

        user_result.set_place(place + 1)
        user_result.set_row_tag(tag)

    return ContestResults(contest, contest_descr, frozen, user_results, last_success, last_run)


class ContestDescr(object):
    def __init__(self, contest):
        self.labeled_problems = []
        self._problem_id_to_index = {}

        for i, problem in enumerate(contest.get_problems()):
            self.labeled_problems.append(LabeledProblem(make_letter(i), problem))
            self._problem_id_to_index[problem.id] = i

    def get_problem_index(self, problem_id):
        return self._problem_id_to_index.get(problem_id)


class SolutionKind(object):
    PENDING = 1
    ACCEPTED = 2
    REJECTED = 3

REJECTED_SUBMISSION_PENALTY = 20


class ProblemResult(object):
    def __init__(self):
        self._kind = SolutionKind.REJECTED
        self._num_submissions = 0  # including the accepted one
        self._acceptance_time = None

    def is_ok(self):
        return (self._kind == SolutionKind.ACCEPTED)

    def get_penalty_time(self):
        if self._kind == SolutionKind.ACCEPTED:
            return self._acceptance_time + (self._num_submissions - 1) * REJECTED_SUBMISSION_PENALTY
        else:
            return 0

    def get_acceptance_time(self):
        return self._acceptance_time

    def register_solution(self, kind, penalty_time):
        if self._kind == SolutionKind.PENDING:
            self._num_submissions += 1
        elif self._kind == SolutionKind.REJECTED:
            self._kind = kind
            self._num_submissions += 1
            if kind == SolutionKind.ACCEPTED:
                self._acceptance_time = penalty_time

    def as_html(self):
        result = u''
        if self._kind == SolutionKind.ACCEPTED:
            number = u'+' if self._num_submissions == 1 else u'+{0}'.format(self._num_submissions - 1)
            hours, minutes = divmod(self._acceptance_time, 60)
            result = u'<span class="ir-accepted">{0}</span><br><span class="ir-ts">{1}:{2:02d}</span>'.format(number, hours, minutes)
        elif self._kind == SolutionKind.PENDING:
            result = u'<span class="ir-pending">?{0}</span>'.format(self._num_submissions)
        elif self._kind == SolutionKind.REJECTED:
            if self._num_submissions == 0:
                result = u'.'
            else:
                result = u'<span class="ir-rejected">−{0}</span>'.format(self._num_submissions)
        return mark_safe(result)


class UserResult(object):
    def __init__(self, contest_descr, user):
        self.contest_descr = contest_descr
        self.user = user
        self.problem_results = [ProblemResult() for _ in contest_descr.labeled_problems]

        self._place = None
        self._row_tag = None
        self._solved_problem_count = None
        self._penalty_time = None
        self._last_acceptance = None

    def register_solution(self, problem_index, kind, penalty_time):
        self.problem_results[problem_index].register_solution(kind, penalty_time)

    def finalize(self):
        self._solved_problem_count = sum(pr.is_ok() for pr in self.problem_results)
        self._penalty_time = sum(pr.get_penalty_time() for pr in self.problem_results)
        accepts = [pr.get_acceptance_time() for pr in self.problem_results if pr.get_acceptance_time() is not None]
        self._last_acceptance = max(accepts) if accepts else 0

    def set_place(self, place):
        self._place = place

    def set_row_tag(self, tag):
        self._row_tag = tag

    def get_solved_problem_count(self):
        return self._solved_problem_count

    def get_penalty_time(self):
        return self._penalty_time

    def get_key(self):
        return (-self._solved_problem_count, self._penalty_time, self._last_acceptance)

    def get_place(self):
        return self._place

    def get_row_tag(self):
        return self._row_tag

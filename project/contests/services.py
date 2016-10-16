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

from .models import Contest, ContestSolution, Membership

LabeledProblem = namedtuple('LabeledProblem', 'letter problem')

LETTERS = u'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
RECENT_CHANGES_WINDOW = timezone.timedelta(minutes=30)


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


def make_problem_choices(contest, empty_label=None):
    if empty_label is None:
        empty_label = make_empty_select(_('Problem'))

    result = []
    result.append((None, empty_label))
    for i, problem in enumerate(contest.get_problems()):
        text = make_lettered_name(make_letter(i), problem.unnumbered_brief_name())
        result.append((problem.id, text))
    return tuple(result)


def make_contestant_choices(contest, empty_label=None):
    if empty_label is None:
        empty_label = make_empty_select(_('Contestant'))

    result = []
    result.append((None, empty_label))
    for user in contest.members.filter(contestmembership__role=Membership.CONTESTANT):
        result.append((user.id, user.get_full_name()))
    return tuple(result)


def total_minutes(td):
    # TODO: add days, ...
    return td.seconds // 60


def total_seconds(td):
    # TODO: add days, ...
    return td.seconds


class ProblemResolver(object):
    def __init__(self, contest):
        self._problems = {}
        self._letters = {}
        for i, problem in enumerate(contest.get_problems()):
            letter = make_letter(i)
            problem_id = force_text(problem.id)
            self._letters[problem_id] = letter
            self._problems[problem_id] = make_lettered_name(letter, problem.short_name)

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

    def get_letter(self, problem_id):
        return self._letters.get(force_text(problem_id), '')


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


ColumnPresence = namedtuple('ColumnPresence', 'solved_problem_count penalty_time total_score')
RunDescription = namedtuple('RunDescription', 'user labeled_problem when kind solution_id')
ContestResults = namedtuple('ContestResults', 'contest contest_descr frozen user_results all_runs last_success last_run column_presence')

# cs here means 'ContestSolution'


def _get_judgement(cs):
    # TODO: Speedup select_related('fixed_judgement')
    # return cs.fixed_judgement if cs.fixed_judgement is not None else cs.solution.best_judgement
    return cs.solution.best_judgement


def _get_kind(cs, freeze_time, show_pending_runs):
    if (freeze_time is not None) and (cs.solution.reception_time >= freeze_time):
        return SolutionKind.PENDING if show_pending_runs else None

    judgement = _get_judgement(cs)

    if judgement is not None and judgement.status == Judgement.DONE:
        if judgement.outcome == Outcome.COMPILATION_ERROR:
            # skip CE (compatibility, this case is included into 'sample_tests_passed is False')
            return None
        if judgement.sample_tests_passed is False:
            return None
        if judgement.outcome == Outcome.ACCEPTED:
            return SolutionKind.ACCEPTED
        elif judgement.outcome == Outcome.CHECK_FAILED:
            return SolutionKind.PENDING
        else:
            return SolutionKind.REJECTED
    else:
        return SolutionKind.PENDING


def _get_score(cs):
    judgement = _get_judgement(cs)
    assert (judgement is not None) and (judgement.status == Judgement.DONE)
    return judgement.score


def _make_contest_results(contest, frozen, user_result_class, column_presence):
    contest_descr = ContestDescr(contest)

    # fetch all contestants from the contest
    users = contest.members.filter(contestmembership__role=Membership.CONTESTANT).select_related('userprofile')
    user_id_result = {}
    for user in users:
        user_id_result[user.id] = user_result_class(contest_descr, user)

    # fetch solutions
    queryset = ContestSolution.objects.\
        filter(contest=contest).\
        filter(solution__reception_time__gte=contest.start_time, solution__reception_time__lt=contest.start_time+contest.duration).\
        select_related('solution', 'solution__best_judgement').\
        order_by('solution__reception_time')

    freeze_time = None
    if frozen and (contest.freeze_time is not None):
        freeze_time = contest.start_time + contest.freeze_time

    all_runs = []
    last_success = None
    last_run = None

    ts_now = timezone.now()

    for cs in queryset:
        user_result = user_id_result.get(cs.solution.author_id)
        if user_result is None:
            # The user is a juror or a contestant that has been excluded from the contest.
            continue

        problem_index = contest_descr.get_problem_index(cs.solution.problem_id)
        if problem_index is None:
            # The problem has been excluded from the contest.
            continue

        kind = _get_kind(cs, freeze_time, contest.show_pending_runs)
        if kind is None:
            continue

        score = None
        if (kind is SolutionKind.REJECTED) or (kind is SolutionKind.ACCEPTED):
            # no score for pending runs
            score = _get_score(cs)

        received = cs.solution.reception_time
        when = received - contest.start_time
        penalty_time = total_minutes(when)

        problem_result = user_result.get_problem_result(problem_index)
        problem_result.register_solution(kind, penalty_time, score)
        if received + RECENT_CHANGES_WINDOW >= ts_now:
            problem_result.notify_recently_updated()

        run = RunDescription(user_result.user, contest_descr.labeled_problems[problem_index], when, kind, cs.solution_id)
        all_runs.append(run)
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
        if (i > 0) and (user_results[i - 1].get_tag_key() != user_results[i].get_tag_key()):
            tag = tag ^ 1

        user_result.set_place(place + 1)
        user_result.set_row_tag(tag)

    return ContestResults(contest, contest_descr, frozen, user_results, all_runs, last_success, last_run, column_presence)


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


class ProblemResultBase(object):
    def __init__(self):
        self._updated_recently = False

    def notify_recently_updated(self):
        self._updated_recently = True

    def is_recently_updated(self):
        return self._updated_recently


class ACMProblemResult(ProblemResultBase):
    def __init__(self):
        super(ACMProblemResult, self).__init__()
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

    def register_solution(self, kind, penalty_time, score):
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


class IOIProblemResult(ProblemResultBase):
    def __init__(self):
        super(IOIProblemResult, self).__init__()
        self._score = None

    def get_score(self):
        return self._score

    def register_solution(self, kind, penalty_time, score):
        if score is not None:
            self._score = score

    def as_html(self):
        if self._score is None:
            result = u'.'
        else:
            result = u'{0}'.format(self._score)
        return mark_safe(result)


class UserResultBase(object):
    def __init__(self, user, problem_results):
        self.user = user
        self.problem_results = problem_results
        self.members = user.userprofile.members
        self._place = None
        self._row_tag = None

    def get_problem_result(self, problem_index):
        return self.problem_results[problem_index]

    def set_place(self, place):
        self._place = place

    def set_row_tag(self, tag):
        self._row_tag = tag

    def get_place(self):
        return self._place

    def get_row_tag(self):
        return self._row_tag

    def finalize(self):
        pass

    def get_key(self):
        raise NotImplementedError()

    def get_tag_key(self):
        raise NotImplementedError()


class ACMUserResult(UserResultBase):
    def __init__(self, contest_descr, user):
        super(ACMUserResult, self).__init__(user, [ACMProblemResult() for _ in contest_descr.labeled_problems])

        self._solved_problem_count = None
        self._penalty_time = None
        self._last_acceptance = None

    def finalize(self):
        self._solved_problem_count = sum(pr.is_ok() for pr in self.problem_results)
        self._penalty_time = sum(pr.get_penalty_time() for pr in self.problem_results)
        accepts = [pr.get_acceptance_time() for pr in self.problem_results if pr.get_acceptance_time() is not None]
        self._last_acceptance = max(accepts) if accepts else 0

    def get_solved_problem_count(self):
        return self._solved_problem_count

    def get_penalty_time(self):
        return self._penalty_time

    def get_key(self):
        return (-self._solved_problem_count, self._penalty_time, self._last_acceptance)

    def get_tag_key(self):
        return self._solved_problem_count


class IOIUserResult(UserResultBase):
    def __init__(self, contest_descr, user):
        super(IOIUserResult, self).__init__(user, [IOIProblemResult() for _ in contest_descr.labeled_problems])

        self._total_score = 0

    def finalize(self):
        self._total_score = sum(((pr.get_score() or 0) for pr in self.problem_results))

    def get_total_score(self):
        return self._total_score

    def get_key(self):
        return (-self._total_score,)

    def get_tag_key(self):
        return self.get_key()


class IContestService(object):
    def get_no_standings_yet_message(self):
        raise NotImplementedError()

    def are_standings_available(self, permissions, timing):
        raise NotImplementedError()

    def should_stop_on_fail(self):
        raise NotImplementedError()

    def should_show_my_solutions_completely(self, timing):
        raise NotImplementedError()

    def make_contest_results(self, contest, frozen):
        raise NotImplementedError()


def create_contest_service(contest):
    if contest.rules == Contest.ACM:
        return ACMContestService()
    if contest.rules == Contest.IOI:
        return IOIContestService()


class ACMContestService(IContestService):
    def get_no_standings_yet_message(self):
        return _('The scoreboard will be available after the start of the contest')

    def are_standings_available(self, permissions, timing):
        if timing.get() == ContestTiming.BEFORE:
            return permissions.standings_before
        return True

    def should_stop_on_fail(self):
        return True

    def should_show_my_solutions_completely(self, timing):
        return True

    def make_contest_results(self, contest, frozen):
        return _make_contest_results(contest, frozen, ACMUserResult, ColumnPresence(True, True, False))


class IOIContestService(IContestService):
    def get_no_standings_yet_message(self):
        return _('The scoreboard is hidden')

    def are_standings_available(self, permissions, timing):
        if timing.get() in (ContestTiming.BEFORE, ContestTiming.IN_PROGRESS):
            return permissions.standings_before
        return True

    def should_stop_on_fail(self):
        return False

    def should_show_my_solutions_completely(self, timing):
        return (timing.get() == ContestTiming.AFTER) and (not timing.is_freeze_applicable())

    def make_contest_results(self, contest, frozen):
        if frozen:
            return None
        return _make_contest_results(contest, False, IOIUserResult, ColumnPresence(False, False, True))

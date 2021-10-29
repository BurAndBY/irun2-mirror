from datetime import timedelta
from collections import namedtuple

from django.template import defaultfilters
from django.utils import timezone
from django.utils.translation import gettext, ngettext

from common.outcome import Outcome
from common.templatetags.irunner_time import _humanized_string
from solutions.models import Judgement

ONE_DAY = timedelta(days=1)

AttemptQuotaInfo = namedtuple('AttemptQuotaInfo', 'quota period next_try')


def _quota(n):
    return AttemptQuotaInfo(n, None, None)


def _quota_during_period(n, period, next_try=None):
    return AttemptQuotaInfo(n, period, next_try)


class ILimitPolicy:
    def get_solution_queryset(self):
        raise NotImplementedError()

    @property
    def attempt_limit(self):
        # None means no limit,
        # 0 means no attempts are allowed.
        raise NotImplementedError()

    @property
    def time_period(self):
        return ONE_DAY

    @property
    def total_attempt_limit(self):
        return None

    @property
    def file_size_limit(self):
        return None

    def _get_problem_solution_queryset(self, problem_id):
        qs = self.get_solution_queryset().\
            exclude(best_judgement__status=Judgement.DONE, best_judgement__sample_tests_passed=False)
        if problem_id is not None:
            qs = qs.filter(problem_id=problem_id)
        return qs

    def _get_total_attempt_qouta(self, problem_id):
        if self.total_attempt_limit is None:
            return _quota(None)
        if self.total_attempt_limit <= 0:
            return _quota(0)

        solution_count = self._get_problem_solution_queryset(problem_id).count()
        return _quota(max(self.total_attempt_limit - solution_count, 0))

    def _get_temp_attempt_qouta(self, problem_id):
        if self.attempt_limit is None:
            return _quota(None)
        if self.attempt_limit <= 0:
            return _quota(0)

        ts = timezone.now() - self.time_period
        times = self._get_problem_solution_queryset(problem_id).\
            filter(reception_time__gte=ts).\
            order_by('-reception_time')[:self.attempt_limit].\
            values_list('reception_time', flat=True)

        times = list(times)
        if len(times) < self.attempt_limit:
            return _quota_during_period(self.attempt_limit - len(times), self.time_period)

        return _quota_during_period(0, self.time_period, times[self.attempt_limit - 1] + self.time_period)

    def get_attempt_quota(self, problem_id):
        q1 = self._get_total_attempt_qouta(problem_id)
        q2 = self._get_temp_attempt_qouta(problem_id)
        if q1.quota is None:
            return q2
        if q2.quota is None:
            return q1
        return q1 if q1.quota <= q2.quota else q2

    def get_attempt_message(self, problem_id):
        return _compose_message(self.get_attempt_quota(problem_id))

    def can_submit(self, problem_id):
        return self.get_attempt_quota(problem_id).quota != 0


class UnlimitedPolicy(ILimitPolicy):
    @property
    def attempt_limit(self):
        return None

    @property
    def file_size_limit(self):
        return None


def _compose_message(aqi: AttemptQuotaInfo) -> str:
    attempts, period, next_try = aqi
    sentences = []

    if attempts is not None:
        if attempts > 0:
            message = ngettext(
                'You have %(count)d attempt remaining',
                'You have %(count)d attempts remaining',
                attempts) % {'count': attempts}

            if period is not None:
                message += ' '
                if period == ONE_DAY:
                    message += gettext('during the day')
                else:
                    message += gettext('(interval: %(duration)s)') % {'duration': _humanized_string(period)}
            message += '.'
            sentences.append(message)

        else:
            sentences.append(gettext('You have no attempts remaining for the problem.'))
            if next_try is not None:
                tz = timezone.get_current_timezone()
                ts = defaultfilters.date(next_try.astimezone(tz), 'DATETIME_FORMAT' if period >= ONE_DAY else 'TIME_FORMAT')
                sentences.append(gettext('Please try again after %(ts)s.') % {'ts': ts})
    else:
        sentences.append(gettext('The number of attempts is not limited.'))

    return ' '.join(sentences)

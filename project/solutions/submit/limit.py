from datetime import timedelta
from collections import namedtuple

from django.template import defaultfilters
from django.utils import timezone
from django.utils.translation import gettext, ngettext

from common.outcome import Outcome
from common.templatetags.irunner_time import _humanized_string
from solutions.models import Judgement

ONE_DAY = timedelta(days=1)

AttemptQuotaInfo = namedtuple('AttemptQuotaInfo', 'quota next_try')


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
    def file_size_limit(self):
        return None

    def get_attempt_quota(self, problem_id):
        if self.attempt_limit is None:
            return AttemptQuotaInfo(None, None)

        if self.attempt_limit <= 0:
            return AttemptQuotaInfo(0, None)

        ts = timezone.now() - timedelta(days=1)

        qs = self.get_solution_queryset()
        if problem_id is not None:
            qs = qs.filter(problem_id=problem_id)

        times = qs.filter(reception_time__gte=ts).\
            exclude(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.COMPILATION_ERROR).\
            order_by('-reception_time')[:self.attempt_limit].\
            values_list('reception_time', flat=True)

        times = list(times)
        if len(times) >= self.attempt_limit:
            return AttemptQuotaInfo(0, times[-1] + self.time_period)
        else:
            return AttemptQuotaInfo(self.attempt_limit - len(times), None)

    def get_attempt_message(self, problem_id):
        return _compose_message(self.get_attempt_quota(problem_id), self.time_period)

    def can_submit(self, problem_id):
        return self.get_attempt_quota(problem_id).quota != 0


class UnlimitedPolicy(ILimitPolicy):
    @property
    def attempt_limit(self):
        return None

    @property
    def file_size_limit(self):
        return None


def _compose_message(aqi: AttemptQuotaInfo, time_period) -> str:
    attempts, next_try = aqi
    if attempts is not None:
        if attempts > 0:
            if time_period == ONE_DAY:
                message = ngettext(
                    'You have %(count)d attempt remaining for the problem during the day.',
                    'You have %(count)d attempts remaining for the problem during the day.',
                    attempts) % {'count': attempts}
            else:
                message = ngettext(
                    'You have %(count)d attempt remaining (interval: %(duration)s).',
                    'You have %(count)d attempts remaining (interval: %(duration)s).',
                    attempts) % {'count': attempts, 'duration': _humanized_string(time_period)}
        else:
            message = gettext('You have no attempts remaining for the problem.')
            if next_try is not None:
                tz = timezone.get_current_timezone()
                ts = defaultfilters.date(next_try.astimezone(tz), 'DATETIME_FORMAT')

                message += ' '
                message += gettext('Please try again after %(ts)s.') % {'ts': ts}
    else:
        message = gettext('The number of attempts is not limited.')
    return message

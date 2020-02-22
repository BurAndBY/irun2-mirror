# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from django.db.models.functions import TruncDay
from django.db.models import Count, F, Q
from django.shortcuts import render
from django.utils import timezone
from django.views import generic

from common.outcome import Outcome
from common.statutils import build_proglangbars, build_outcomebars

from solutions.models import Solution, Judgement


class SingleDayInfo(object):
    def __init__(self, date):
        self.date = date
        self.accepted = 0
        self.rejected = 0
        self._max_value = None

    def set_max_value(self, max_value):
        self._max_value = max_value if max_value > 0 else 1

    @staticmethod
    def _perc(x):
        return '{:.2f}%'.format(x)

    def get_accepted_perc(self):
        return self._perc(100. * self.accepted / self._max_value)

    def get_all_perc(self):
        return self._perc(100. * (self.accepted + self.rejected) / self._max_value)


def _make_solutions_qs(qs, start_date):
    assert isinstance(start_date, datetime.date)
    start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
    ts = timezone.make_aware(start_datetime)

    first_id = qs.\
        filter(reception_time__gte=ts).\
        values_list('id', flat=True).\
        first()

    if first_id is not None:
        return qs.filter(id__gte=first_id)
    return qs.none()


def _make_chart(queryset, start_date, end_date):
    day = datetime.timedelta(days=1)
    mp = {}
    results = []
    today = start_date
    while (today <= end_date) and (len(results) <= 1000):
        info = SingleDayInfo(today)
        results.append(info)
        mp[today] = info
        today += day

    tzinfo = timezone.get_current_timezone()
    for day, num_accepted, num_rejected in queryset.\
            filter(best_judgement__status=Judgement.DONE).\
            annotate(
                day=TruncDay('reception_time', tzinfo=tzinfo),
                outcome=F('best_judgement__outcome')
            ).\
            values_list('day').\
            annotate(
                num_accepted=Count('pk', filter=Q(outcome=Outcome.ACCEPTED)),
                num_rejected=Count('pk', filter=~Q(outcome=Outcome.ACCEPTED))
            ).\
            values_list('day', 'num_accepted', 'num_rejected'):

        info = mp.get(day.date())
        if info is not None:
            info.accepted += num_accepted
            info.rejected += num_rejected

    max_value = 0
    for info in results:
        max_value = max(max_value, info.accepted + info.rejected)
    for info in results:
        info.set_max_value(max_value)
    return results


def _get_term_start(today):
    assert isinstance(today, datetime.date)
    if today.month >= 9:
        term_start = datetime.date(today.year, 9, 1)
    elif today.month <= 1:
        term_start = datetime.date(today.year - 1, 9, 1)
    else:
        term_start = datetime.date(today.year, 2, 1)
    return term_start


class ActivityView(generic.View):
    template_name = 'solutions/activity.html'
    bar_max_px = 16

    def get(self, request):
        ts = timezone.now()
        today = timezone.localtime(ts).date()

        year_start = today - datetime.timedelta(days=365)
        year_solution_queryset = _make_solutions_qs(Solution.objects, year_start)
        results_year = _make_chart(year_solution_queryset, year_start, today)

        term_start = _get_term_start(today)
        term_solution_queryset = _make_solutions_qs(Solution.objects, term_start).filter(coursesolution__isnull=False)
        results_term = _make_chart(term_solution_queryset, term_start, today)

        all_proglangbars = build_proglangbars(term_solution_queryset)
        accepted_proglangbars = build_proglangbars(term_solution_queryset.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.ACCEPTED))

        outcomebars = build_outcomebars(term_solution_queryset)

        context = {
            'results_year': results_year,
            'results_term': results_term,
            'max_width_px': self.bar_max_px * len(results_term),
            'term_start': term_start,
            'all_proglangbars': all_proglangbars,
            'accepted_proglangbars': accepted_proglangbars,
            'outcomebars': outcomebars,
        }
        return render(request, self.template_name, context)

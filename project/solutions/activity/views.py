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
        self._height = None

    def set_height(self, height):
        self._height = float(height)

    def set_max_value(self, max_value):
        self._max_value = max_value if max_value > 0 else 1

    def get_accepted_px(self):
        return self._height * self.accepted / self._max_value

    def get_all_px(self):
        return self._height * (self.accepted + self.rejected) / self._max_value


def _make_chart(queryset, start_date, end_date, chart_height):
    day = datetime.timedelta(days=1)
    mp = {}
    results = []
    today = start_date
    while (today <= end_date) and (len(results) <= 1000):
        info = SingleDayInfo(today)
        results.append(info)
        mp[today] = info
        today += day

    db_start_date = start_date - day
    tzinfo = timezone.get_current_timezone()
    for day, num_accepted, num_rejected in queryset.\
            filter(reception_time__gte=db_start_date, best_judgement__status=Judgement.DONE).\
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
        info.set_height(chart_height)
    return results


def _get_term_start(today):
    if today.month >= 9:
        term_start = datetime.date(today.year, 9, 1)
    elif today.month <= 1:
        term_start = datetime.date(today.year - 1, 9, 1)
    else:
        term_start = datetime.date(today.year, 2, 1)
    return term_start


class ActivityView(generic.View):
    template_name = 'solutions/activity.html'
    chart_height = 200

    def get(self, request):
        ts = timezone.now()
        today = timezone.localtime(ts).date()

        results_year = _make_chart(Solution.objects.all(), today - datetime.timedelta(days=365), today, self.chart_height)

        term_start = _get_term_start(today)
        results_term = _make_chart(Solution.objects.filter(coursesolution__isnull=False), term_start, today, self.chart_height)

        term_solution_queryset = Solution.objects.\
            filter(coursesolution__isnull=False).\
            filter(reception_time__gte=term_start)

        all_proglangbars = build_proglangbars(term_solution_queryset)
        accepted_proglangbars = build_proglangbars(term_solution_queryset.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.ACCEPTED))

        outcomebars = build_outcomebars(term_solution_queryset)

        context = {
            'results_year': results_year,
            'results_term': results_term,
            'term_start': term_start,
            'chart_height': self.chart_height,
            'all_proglangbars': all_proglangbars,
            'accepted_proglangbars': accepted_proglangbars,
            'outcomebars': outcomebars,
        }
        return render(request, self.template_name, context)

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import auth
from django.db.models import Count
from django.shortcuts import render
from django.views import generic

from cauth.mixins import StaffMemberRequiredMixin
from problems.models import Problem
from solutions.models import Solution


class HallOfFameView(StaffMemberRequiredMixin, generic.View):
    template_name = 'solutions/hall_of_fame.html'

    def get(self, request):

        user_ids = {}
        problem_ids = {}

        q = Solution.objects.values('author_id', 'problem_id').annotate(cnt=Count('*')).order_by('-cnt')[:20]

        for record in q:
            user_ids[record['author_id']] = None
            problem_ids[record['problem_id']] = None

        for user in auth.get_user_model().objects.filter(pk__in=user_ids):
            user_ids[user.id] = user
        for problem in Problem.objects.filter(pk__in=problem_ids):
            problem_ids[problem.id] = problem

        top_attempts = []
        for record in q:
            top_attempts.append((
                record['cnt'],
                user_ids[record['author_id']],
                problem_ids[record['problem_id']],
            ))

        context = {'top_attempts': top_attempts}
        return render(request, self.template_name, context)

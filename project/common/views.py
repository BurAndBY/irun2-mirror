import datetime

from django.http import Http404
from django.shortcuts import render, redirect
from django.views import generic
from django.db.models import Count
from django.contrib import auth
from django.utils import timezone

from cauth.mixins import StaffMemberRequiredMixin
from contests.models import Contest, UnauthorizedAccessLevel
from courses.models import Course, CourseStatus
from courses.messaging import MessageCountManager
from news.models import NewsMessage
from solutions.models import Solution, Judgement
from problems.models import Problem

from .outcome import Outcome
from .pageutils import IRunnerPaginator
from .statutils import build_proglangbars, build_outcomebars

NUM_CONTESTS = 3


class IRunnerBaseListView(generic.list.MultipleObjectMixin, generic.View):
    allow_all = True
    paginate_by = 25

    def get_context_data(self, **kwargs):
        queryset = kwargs.pop('object_list', self.object_list)
        p = IRunnerPaginator(self.paginate_by, self.allow_all)
        context = p.paginate(self.request, queryset)
        context.update(**kwargs)
        return super(generic.list.MultipleObjectMixin, self).get_context_data(**context)

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return self.render_to_response(context)


class IRunnerListView(generic.list.MultipleObjectTemplateResponseMixin, IRunnerBaseListView):
    pass


class MassOperationView(generic.View):
    template_name = None
    form_class = None
    question = None
    success_url = '/'

    @staticmethod
    def _make_int_list(ids):
        result = set()
        for x in ids:
            try:
                x = int(x)
            except:
                raise Http404('bad id')
            result.add(x)

        return list(result)

    def get_context_data(self, **kwargs):
        return kwargs

    def _make_context(self, query_dict, queryset):
        # take really existing ids
        ids = [object.pk for object in queryset]

        context = {
            'object_list': [self.prepare_to_display(obj) for obj in queryset],
            'ids': ids,
            'next': query_dict.get('next'),
            'question': self.question,
        }
        context = self.get_context_data(**context)
        return context

    def _redirect(self, response):
        if response is not None:
            return response

        next = self.request.POST.get('next')
        if next is None:
            next = self.success_url
        return redirect(next)

    def get(self, request, *args, **kwargs):
        ids = MassOperationView._make_int_list(request.GET.getlist('id'))

        queryset = self.get_queryset().filter(pk__in=ids)

        context = self._make_context(request.GET, queryset)

        if self.form_class is not None:
            form = self.form_class()
            context['form'] = form

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        ids = MassOperationView._make_int_list(request.POST.getlist('id'))

        queryset = self.get_queryset().filter(pk__in=ids)

        if self.form_class is not None:
            form = self.form_class(request.POST)
            if form.is_valid():
                response = self.perform(queryset, form)
                return self._redirect(response)
            else:
                context = self._make_context(request.POST, queryset)
                context['form'] = form
                return render(request, self.template_name, context)

        response = self.perform(queryset, None)
        return self._redirect(response)

    '''
    Methods that may be overridden.
    '''
    def perform(self, filtered_queryset, form):
        # form is passed only if form_class is not None.
        # form is valid.
        raise NotImplementedError()

    def get_queryset(self):
        raise NotImplementedError()

    def prepare_to_display(self, obj):
        return obj

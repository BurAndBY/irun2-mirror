from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render, redirect
from django.views import generic
from django.db.models import Count
from django.contrib import auth

from cauth.mixins import StaffMemberRequiredMixin
from contests.models import Contest, UnauthorizedAccessLevel
from courses.models import Course, Membership
from courses.messaging import get_unread_thread_count
from courses.calcpermissions import calculate_course_permissions
from solutions.models import Solution
from problems.models import Problem


def home(request):
    context = {}

    if request.user.is_authenticated():
        memberships_per_course = {}

        # TODO: filter active courses
        for membership in Membership.objects.filter(user=request.user):
            memberships_per_course.setdefault(membership.course_id, []).append(membership)

        courses = Course.objects.filter(pk__in=memberships_per_course)  # default ordering

        courses_with_unread = []
        for course in courses:
            memberships = memberships_per_course[course.id]
            permissions = calculate_course_permissions(course, request.user, memberships)
            unread = get_unread_thread_count(course, request.user, permissions)
            courses_with_unread.append((course, unread))

        context['courses_with_unread'] = courses_with_unread

        contests = Contest.objects.filter(membership__user=request.user).order_by('-start_time').distinct()
        context['my_contests'] = contests

    public_contests = Contest.objects.exclude(unauthorized_access=UnauthorizedAccessLevel.NO_ACCESS).order_by('-start_time')
    context['public_contests'] = public_contests
    return render(request, 'common/home.html', context)


def about(request):
    return render(request, 'common/about.html', {})


def language(request):
    next = request.GET.get('next')
    return render(request, 'common/language.html', {'redirect_to': next})


class HallOfFameView(StaffMemberRequiredMixin, generic.View):
    template_name = 'common/hall_of_fame.html'

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


class IRunnerPaginationContext(object):
    def __init__(self):
        self.page_obj = None
        self.object_count = 0
        self.per_page_count = 0
        self.query_param_size = ''
        self.query_params_other = ''
        self.page_size_constants = []


class IRunnerBaseListView(generic.list.BaseListView):
    page_size_constants = [7, 12, 25, 50, 100]
    size_kwarg = 'size'

    def _parse_size_param(self):
        '''
        Parses size param from query string.
        '''
        size = self.request.GET.get(self.size_kwarg)
        if size is None:
            return None  # param was not passed

        try:
            size = int(size)
        except (TypeError, ValueError):
            raise Http404('That page size is not an integer')
        if size < 0:
            raise Http404('That page size is less than zero')
        return size

    def get_paginate_by(self, queryset):
        '''
        Paginate by specified value in querystring, or use default class property value.
        '''
        size = self._parse_size_param()
        if size is not None:
            return None if size == 0 else size
        else:
            return self.paginate_by

    def _list_page_sizes(self, size):
        '''
        Prepares ordered list of integers.
        '''
        s = set(self.page_size_constants)
        s.add(size)
        s.add(self.paginate_by)
        return sorted(filter(None, s))

    def _get_size_query_param(self):
        '''
        Returns '' or '&size=N' string.
        '''
        result = ''
        size = self._parse_size_param()
        if size is not None:
            # safe: no need to urlencode integers
            result = '&{0}={1}'.format(self.size_kwarg, size)
        return result

    def _get_other_query_params(self):
        '''
        Returns '' or '&key1=value1&key2=value2...' string made up with
        params that are not related to pagination.
        '''
        params = self.request.GET.copy()
        if self.size_kwarg in params:
            params.pop(self.size_kwarg)
        if self.page_kwarg in params:
            params.pop(self.page_kwarg)

        result = params.urlencode()
        if result:
            result = '&' + result
        return result

    def _get_object_count(self, context):
        '''
        Always returns integer.
        '''
        paginator = context.get('paginator')
        if paginator is None:
            queryset = context['object_list']
            # create fake paginator to get total object list
            paginator = Paginator(queryset, 1)
        return paginator.count

    def _get_per_page_count(self, context):
        '''
        Always returns integer.
        '''
        paginator = context.get('paginator')
        if paginator is None:
            return 0
        else:
            return paginator.per_page

    def get_context_data(self, **kwargs):
        context = super(IRunnerBaseListView, self).get_context_data(**kwargs)

        pc = IRunnerPaginationContext()

        pc.page_obj = context.get('page_obj')

        pc.object_count = self._get_object_count(context)
        pc.per_page_count = self._get_per_page_count(context)

        pc.query_param_size = self._get_size_query_param()
        pc.query_params_other = self._get_other_query_params()

        pc.page_size_constants = self._list_page_sizes(pc.per_page_count)

        context['pagination_context'] = pc
        return context


class IRunnerListView(generic.list.MultipleObjectTemplateResponseMixin, IRunnerBaseListView):
    pass


def error403(request):
    return render(request, 'common/error403.html', {}, status=403)


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

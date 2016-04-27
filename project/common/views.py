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

from .pageutils import IRunnerPaginator


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


class IRunnerBaseListView(generic.list.MultipleObjectMixin, generic.View):
    allow_all = True
    paginate_by = 0

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

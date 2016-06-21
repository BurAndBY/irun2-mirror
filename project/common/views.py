import datetime

from django.http import Http404
from django.shortcuts import render, redirect
from django.views import generic
from django.db.models import Count
from django.contrib import auth
from django.utils import timezone

from cauth.mixins import StaffMemberRequiredMixin
from contests.models import Contest, UnauthorizedAccessLevel
from courses.models import Course, Membership
from courses.messaging import get_unread_thread_count
from courses.calcpermissions import calculate_course_permissions
from news.models import NewsMessage
from solutions.models import Solution, Judgement
from problems.models import Problem

from .outcome import Outcome
from .pageutils import IRunnerPaginator
from .statutils import build_proglangbars, build_outcomebars


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

    news = NewsMessage.objects.filter(is_public=True).order_by('-when')
    context['news'] = news

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
    for ts, outcome in queryset.\
            filter(reception_time__gte=db_start_date, best_judgement__status=Judgement.DONE).\
            values_list('reception_time', 'best_judgement__outcome'):
        loc = timezone.localtime(ts)
        info = mp.get(loc.date())
        if info is not None:
            if outcome == Outcome.ACCEPTED:
                info.accepted += 1
            else:
                info.rejected += 1

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
    template_name = 'common/activity.html'
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

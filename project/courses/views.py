# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render, render_to_response, redirect
from django.views import generic
from django.http import HttpResponseRedirect, Http404
from .models import Course, Topic, Membership, Assignment
from .forms import TopicForm, ActivityForm, PropertiesForm, CompilersForm, ProblemAssignmentForm, AddExtraProblemSlotForm
from django.conf import settings

from django.core.urlresolvers import reverse
from django.forms.models import model_to_dict
from proglangs.models import Compiler
from django.db import transaction
from problems.views import ProblemStatementMixin
from problems.models import Problem
from collections import namedtuple
from django.forms import inlineformset_factory
from django.contrib import messages

import random


class FakeUser(object):
    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name


USERS = [FakeUser(t.split()[1], t.split()[0]) for t in (
    u'Безрукова Виктория Яновна',
    u'Гусляков Борислав Геннадиевич',
    u'Жжёнов Ипполит Артемович',
    u'Ильюшина Дарья Казимировна',
    u'Каца Арина Евгениевна',
    u'Климцов Денис Онуфриевич',
    u'Коденко Нина Кузьмевна',
    u'Краснокутский Андрей Архипович',
    u'Куклачёва Екатерина Ивановна',
    u'Кулатова Лилия Ипполитовна',
    u'Мажов Игорь Платонович',
    u'Манякин Роман Никонович',
    u'Машков Никита Фролович',
    u'Никонов Андрей Проклович',
    u'Полищук Илья Фролович',
    u'Старцев Георгий Богданович',
    u'Угольников Роман Афанасиевич',
    u'Цветкова Кристина Филипповна',
    u'Ясакова Ольга Владленовна',
    u'Яшнова Доминика Трофимовна',
    )
]

PROBLEMS = (
    (u'07', 7),
    (u'11. Разложение', 7),
    (u'31. Валюта', 4),
    (u'7. Карточки', 4),
    (u'21. Цилиндр', 5),
    (u'02.1. Робот-1', 8),
    (u'9. Олимпиада', 5),
    (u'32', 9),
    (u'51. Пасьянс', 9),
    (u'56. Фишка', 6),
    (u'26. Черный ящик', 9),
    (u'24. Компании', 7),
    (u'15. Магистраль', 9),
    (u'16. Перекресток', 7),
    (u'25', 6),
    (u'71. Лесенки', 6),
    (u'55. Треугольник', 5),
    (u'01. Считалка', 4),
    (u'13. Караван-1', 6),
    (u'13. Янка', 6),
    (u'21. Пр.перекр.', 7),
    (u'37', 10),
    (u'39.1. Телефон', 10),
    (u'36. Домино', 8),
    (u'34. Урок математ', 10),
    (u'16. Конь-1', 5),
    (u'3.1.Маршр.(реб.)', 8),
    (u'25. Прогулка', 10),
    (u'01', 5),
    (u'09. Деление', 6),
    (u'3. Прох. из 1стр', 4),
    (u'13. Караван-1', 6),
    (u'54. Отр. скидки', 7),
    (u'12. Встреча', 7),
    (u'9. Олимпиада', 5),
    (u'21', 7),
    (u'38. Полоса', 7),
    (u'02. Сдача', 6),
    (u'4. Таблица', 7),
    (u'15. Робот', 7),
    (u'6. Открытки', 8),
    (u'16. Перекресток', 7),
    (u'13', 10),
    (u'59.2. Репортаж', 10),
    (u'40. Ребёнок', 7),
    (u'38. Корпоратив.с', 10),
    (u'8. Форма-1', 8),
    (u'48. Платформы', 10),
    (u'14. Второй маршр', 8),
    (u'14', 10),
    (u'43. Цифровой экр', 10),
    (u'04. Триангуляция', 8),
    (u'52. Flood It!', 10),
    (u'12. Чиновники', 8),
    (u'11. Станки', 10),
    (u'20. Без лев.пов.', 8),
    (u'05', 8),
    (u'48. Дор. конт.', 9),
    (u'21. Юбилей', 7),
    (u'22. Прямоугольни', 9),
    (u'42. Соревнования', 10),
    (u'19. Пирамида', 10),
    (u'23. Поворот', 8),
    (u'07', 7),
    (u'28. Сотовый', 8),
    (u'50. Лестница', 6),
    (u'37. Код', 9),
    (u'18. Конь-3', 5),
    (u'29.1. Слова', 6),
    (u'21. Пр.перекр.', 7),
    (u'04', 8),
    (u'06. Без разрывов', 8),
    (u'44. Солдаты', 6),
    (u'23. Замок', 9),
    (u'14. Караван-2', 6),
    (u'45. Военный похо', 9),
    (u'12. Встреча', 7),
    (u'06', 8),
    (u'42. Лента', 7),
    (u'26. Гвозди', 6),
    (u'15. Робот', 7),
    (u'19. Ладья', 5),
    (u'5. Шестерёнки', 6),
    (u'62. Дерево', 6),
    (u'10', 10),
    (u'39.1. Телефон', 10),
    (u'70. Захват', 8),
    (u'52. Flood It!', 10),
    (u'12. Чиновники', 8),
    (u'15. Магистраль', 9),
    (u'66. Острова', 9),
    (u'22', 7),
    (u'10. Вложение', 7),
    (u'01. Покупка', 6),
    (u'10. Лабиринт-1', 8),
    (u'20. Слон', 5),
    (u'8. Незнакомые', 5),
    (u'30. Цепочка-дом', 6),
    (u'08', 6),
    (u'53.Из 11 в nm', 6),
    (u'69. Кувшинки', 4),
    (u'6. Король', 4),
    (u'3. Квадрат', 5),
    (u'63. Остов', 6),
    (u'68. Степ. посл.', 4),
    (u'34.2', 10),
    (u'47.1. Делимость', 10),
    (u'70. Захват', 8),
    (u'25. Кубик', 10),
    (u'30. Шланги', 6),
    (u'35. Стрельба', 10),
    (u'20. Без лев.пов.', 8),
    (u'11', 8),
    (u'12. Бинарные', 7),
    (u'17. Скидки', 7),
    (u'11. Лабиринт-2', 8),
    (u'17. Конь-2', 6),
    (u'63. Остов', 6),
    (u'4.1. Лабиринт-1', 8),
    (u'34.1', 10),
    (u'39.2. Телефон', 10),
    (u'27. Снег', 7),
    (u'28. Расписание', 10),
    (u'31. Химия', 6),
    (u'66. Острова', 9),
    (u'3.2.Маршр.(вер.)', 8),
    (u'19', 7),
    (u'73. Поезд', 7),
    (u'72. Билеты', 4),
    (u'51. Слияния', 5),
    (u'2. Полоска', 4),
    (u'24. Гонка', 8),
    (u'8. Незнакомые', 5),
    (u'18', 9),
    (u'07. Разрыв-1', 9),
    (u'14. Игра', 6),
    (u'14. Караван-2', 6),
    (u'30. Шланги', 6),
    (u'7. Команды', 9),
    (u'29.2. Слова', 8),
    (u'09', 9),
    (u'08. Разрыв-m', 9),
    (u'16. Эпидемия', 7),
    (u'43. Кодирование', 8),
    (u'7. Карточки', 4),
    (u'18. Хакеры', 10),
    (u'64. Матрица', 4),
    (u'12', 10),
    (u'65. Джокеры', 10),
    (u'30.2. Паркет', 8),
    (u'5.1. Остановки', 9),
    (u'45. Мегаинверси', 10),
    (u'65. Ровно K', 9),
    (u'02.2. Робот-2', 8),
)


class BaseCourseView(generic.View):
    tab = None
    subtab = None

    def _load(self, course_id):
        return get_object_or_404(Course, pk=course_id)

    def _load_topic(self, course, topic_id):
        topic = course.topic_set.filter(id=topic_id).first()
        if topic is None:
            raise Http404('Topic does not exist in the course')
        return topic

    def _load_problem_from_topic(self, course, topic, problem_id):
        return get_object_or_404(Problem, pk=problem_id)

    def _make_context(self, course):
        context = {
            'course': course,
            'active_tab': self.tab,
            'active_subtab': self.subtab
        }
        return context


class CourseInfoView(BaseCourseView):
    tab = 'info'
    template_name = 'courses/info.html'

    def get(self, request, course_id):
        course = self._load(course_id)
        context = self._make_context(course)
        return render(request, self.template_name, context)


class StudentProblemResult(object):
    def __init__(self, short_name, complexity, points, max_points, criteria):
        self.short_name = short_name
        self.complexity = complexity
        self.points = points
        self.max_points = max_points
        self.criteria = criteria
        self.submitted = (points > 0)

    def is_full_solution(self):
        return self.points == self.max_points


class StudentResult(object):
    def __init__(self, name, surname, insubgroup, problemresults):
        self.name = name
        self.surname = surname
        self.insubgroup = insubgroup
        self.problemresults = problemresults
        self.summary = 0


class CourseStandingsView(BaseCourseView):
    tab = 'standings'
    template_name = 'courses/standings.html'

    def get(self, request, course_id):
        course = self._load(course_id)
        rnd = random.Random(1)

        students = Membership.objects\
            .filter(course=course, role=Membership.STUDENT)\
            .select_related(settings.AUTH_USER_MODEL)\
            .order_by('last_name', 'first_name')

        topics = course.topic_set.all().prefetch_related('slot_set')

        slot_indices = {}

        header = []
        for topic in topics:
            slots = list(topic.slot_set.all())
            for slot in slots:
                index = len(slot_indices)
                slot_indices[slot.id] = index

            header.append((topic.name, len(slots)))

        results = []
        for student in USERS:
            sprs = []
            for _ in range(4):
                problem = rnd.choice(PROBLEMS)
                max_points = rnd.randint(1, 100)
                points = rnd.randint(0, max_points)
                algo_accepted = bool(rnd.randint(0, 1))
                criteria = (('A', algo_accepted),)
                sprs.append(StudentProblemResult(problem[0], problem[1], points, max_points, criteria))

            #tokens = student.split(' ')
            surname, name = student.last_name, student.first_name
            insubgroup = False
            sr = StudentResult(name, surname, insubgroup, sprs)
            results.append(sr)

        context = self._make_context(course)
        context['results'] = results
        context['header_topics'] = header
        return render(request, self.template_name, context)

#Activity = namedtuple('Activity', 'name weight')
SheetRow = namedtuple('SheetRow', 'user main_activity_scores final_score extra_activity_scores')


class CourseSheetView(BaseCourseView):
    tab = 'sheet'
    template_name = 'courses/sheet.html'

    def get(self, request, course_id):
        course = self._load(course_id)
        rnd = random.Random(1)

        #main_activities = (
        #    Activity(u'Инд. задания', 0.5),
        #    Activity(u'Контр. раб. 1', 0.3),
        #    Activity(u'Промеж. тест.', 0.1),
        #    Activity(u'Итогов. тест.', 0.1),
        #)

        main_activities = course.activity_set.filter(weight__gt=0.0)
        extra_activities = course.activity_set.filter(weight=0.0)

        #extra_activities = (
        #    Activity(u'Контр. работа №2 AVL-деревья', None),
        #    Activity(u'Домашнее задание', None),
        #)

        rows = []
        for user in USERS:
            rows.append(SheetRow(
                user,
                [rnd.randint(4, 10) for _ in main_activities],
                rnd.randint(4, 10),
                [rnd.randint(4, 10) for _ in extra_activities],
            ))

        context = self._make_context(course)
        context['main_activities'] = main_activities
        context['extra_activities'] = extra_activities
        context['data'] = rows
        return render(request, self.template_name, context)


class CourseSubmitView(BaseCourseView):
    tab = 'submit'
    template_name = 'courses/submit.html'

    def get(self, request, course_id):
        course = self._load(course_id)
        context = self._make_context(course)
        return render(request, self.template_name, context)


class CourseSettingsView(BaseCourseView):
    tab = 'settings'


class CourseSettingsPropertiesView(CourseSettingsView):
    subtab = 'properties'
    template_name = 'courses/settings_properties.html'

    def get(self, request, course_id):
        course = self._load(course_id)
        form = PropertiesForm(instance=course)
        context = self._make_context(course)
        context['form'] = form
        return render(request, self.template_name, context)

    def post(self, request, course_id):
        course = self._load(course_id)
        form = PropertiesForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('courses:course_settings_properties', course_id=course_id)

        context = self._make_context(course)
        context['form'] = form
        return render(request, self.template_name, context)


class CourseSettingsCompilersView(CourseSettingsView):
    subtab = 'compilers'
    template_name = 'courses/settings_compilers.html'

    def get(self, request, course_id):
        course = self._load(course_id)
        form = CompilersForm(instance=course)
        context = self._make_context(course)
        context['form'] = form
        return render(request, self.template_name, context)

    def post(self, request, course_id):
        course = self._load(course_id)
        form = CompilersForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('courses:course_settings_compilers', course_id=course_id)

        context = self._make_context(course)
        return render(request, self.template_name, context)


class CourseSettingsUsersView(CourseSettingsView):
    subtab = 'users'
    template_name = 'courses/settings_users.html'

    def get(self, request, course_id):
        course = self._load(course_id)

        students = course.members.filter(membership__role=Membership.STUDENT).order_by('last_name')
        teachers = course.members.filter(membership__role=Membership.TEACHER).order_by('last_name')

        context = self._make_context(course)
        context['students'] = students
        context['teachers'] = teachers
        return render(request, self.template_name, context)


class CourseSettingsUsersStudentsView(CourseSettingsView):
    subtab = 'users'
    template_name = 'courses/settings_users_edit.html'

    def get(self, request, course_id):
        course = self._load(course_id)

        students = course.members.all()

        context = self._make_context(course)
        context['students'] = students
        return render(request, self.template_name, context)


class CourseSettingsSubgroupsView(CourseSettingsView):
    subtab = 'subgroups'
    template_name = 'courses/settings_subgroups.html'

    def get(self, request, course_id):
        course = self._load(course_id)
        context = self._make_context(course)
        return render(request, self.template_name, context)


from models import Activity


class CourseSettingsSheetView(CourseSettingsView):
    subtab = 'sheet'
    template_name = 'courses/settings_sheet.html'

    def get(self, request, course_id):
        course = self._load(course_id)
        context = self._make_context(course)
        ActivityFormSet = inlineformset_factory(Course, Activity, fields=('name', 'kind', 'weight'))
        formset = ActivityFormSet(instance=course)
        context['formset'] = formset

        return render(request, self.template_name, context)

    def post(self, request, course_id):
        course = self._load(course_id)
        context = self._make_context(course)
        ActivityFormSet = inlineformset_factory(Course, Activity, fields=('name', 'kind', 'weight'))
        formset = ActivityFormSet(request.POST, instance=course)
        if formset.is_valid():
            formset.save()
            return redirect('courses:course_settings_sheet', course_id=course_id)

        context['formset'] = formset
        return render(request, self.template_name, context)


'''
Base views to view and edit course-to-many relationships in course settings.
'''


class CourseSettingsBaseListView(CourseSettingsView):
    '''
    You should:
    * set subtab
    * set template_name
    * override get_queryset()
    '''

    def get_queryset(self, course):
        raise NotImplementedError()

    def get(self, request, course_id):
        course = self._load(course_id)
        object_list = self.get_queryset(course)
        context = self._make_context(course)
        context['object_list'] = object_list
        self._do_init_context(course, object_list, context)
        return render(request, self.template_name, context)

    def _do_init_context(self, course, object_list, context):
        # you can fill pass some additional calculated data to context
        pass


class CourseSettingsBaseCreateView(CourseSettingsView):
    '''
    You should:
    * set subtab
    * set form_class
    * set list_url_name
    '''
    template_name = 'courses/settings_component.html'

    def _make_context_form(self, course, form):
        context = self._make_context(course)
        context['form'] = form
        context['cancel_url'] = reverse(self.list_url_name, args=(course.id,))
        return context

    def get(self, request, course_id):
        course = self._load(course_id)
        form = self.form_class()

        context = self._make_context_form(course, form)
        return render(request, self.template_name, context)

    def post(self, request, course_id):
        course = self._load(course_id)
        form = self.form_class(request.POST)
        if form.is_valid():
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.course = course
                obj.save()
                self._do_save(course, form, obj)
            return redirect(self.list_url_name, course_id=course_id)

        context = self._make_context_form(course, form)
        return render(request, self.template_name, context)

    def _do_save(self, course, form, obj):
        # you can do something after object has been saved (in the same transaction)
        pass


class CourseSettingsBaseUpdateView(CourseSettingsView):
    '''
    You should:
    * set subtab
    * set form_class
    * set list_url_name
    '''
    template_name = 'courses/settings_component.html'

    def _make_context_form(self, course, form):
        context = self._make_context(course)
        context['form'] = form
        context['can_delete'] = True
        context['cancel_url'] = reverse(self.list_url_name, args=(course.id,))
        return context

    def _get_object(self, course_id, pk):
        model = self.form_class.Meta.model
        return get_object_or_404(model, course_id=course_id, pk=pk)

    def get(self, request, course_id, pk):
        course = self._load(course_id)
        obj = self._get_object(course_id, pk)
        form = self.form_class(instance=obj)
        self._do_load(course, form, obj)

        context = self._make_context_form(course, form)
        return render(request, self.template_name, context)

    def post(self, request, course_id, pk):
        course = self._load(course_id)
        obj = self._get_object(course_id, pk)
        form = self.form_class(request.POST, instance=obj)

        if 'save' in request.POST:
            if form.is_valid():
                with transaction.atomic():
                    obj = form.save()
                    self._do_save(course, form, obj)
                return redirect(self.list_url_name, course_id=course_id)

        elif 'delete' in request.POST:
            obj.delete()
            return redirect(self.list_url_name, course_id=course_id)

        context = self._make_context_form(course, form)
        return render(request, self.template_name, context)

    def _do_load(self, course, form, obj):
        pass

    def _do_save(self, course, form, obj):
        pass

'''
Topics
'''


class TopicMixin(object):
    subtab = 'topics'
    form_class = TopicForm
    list_url_name = 'courses:course_settings_topics'

    def _do_save(self, course, form, obj):
        target_num_problems = form.cleaned_data['num_problems']
        topic = obj

        slots = topic.slot_set.all()
        if len(slots) < target_num_problems:
            diff = target_num_problems - len(slots)
            for i in range(diff):
                topic.slot_set.create()
        else:
            for slot in slots[target_num_problems:]:
                slot.delete()

    def _do_load(self, course, form, obj):
        form.fields['num_problems'].initial = obj.slot_set.count()


class CourseSettingsTopicsListView(TopicMixin, CourseSettingsBaseListView):
    template_name = 'courses/settings_topics.html'

    def get_queryset(self, course):
        return course.topic_set.all().prefetch_related('slot_set')


class CourseSettingsTopicsCreateView(TopicMixin, CourseSettingsBaseCreateView):
    pass


class CourseSettingsTopicsUpdateView(TopicMixin, CourseSettingsBaseUpdateView):
    pass


'''
Sheet
'''


class SheetMixin(object):
    subtab = 'sheet'
    form_class = ActivityForm
    list_url_name = 'courses:course_settings_sheet'


class CourseSettingsSheetActivityListView(SheetMixin, CourseSettingsBaseListView):
    template_name = 'courses/settings_sheet.html'

    def get_queryset(self, course):
        return course.activity_set.all()

    def _do_init_context(self, course, object_list, context):

        sum_weights = 0.0
        main_activities = []
        extra_activities = []

        for activity in object_list:
            w = activity.weight
            sum_weights += w
            if w != 0.0:
                main_activities.append(activity)
            else:
                extra_activities.append(activity)

        context['main_activities'] = main_activities
        context['extra_activities'] = extra_activities

        EPS = 1.E-6
        TARGET_SUM = 1.0
        if (sum_weights > EPS) and (abs(sum_weights - TARGET_SUM) > EPS):
            context['sum_actual'] = sum_weights
            context['sum_expected'] = TARGET_SUM
            context['sum_is_bad'] = True


class CourseSettingsSheetActivityCreateView(SheetMixin, CourseSettingsBaseCreateView):
    pass


class CourseSettingsSheetActivityUpdateView(SheetMixin, CourseSettingsBaseUpdateView):
    pass

'''
Problems
'''


class CourseProblemsView(BaseCourseView):
    tab = 'problems'
    template_name = 'courses/problems_base.html'

    def get(self, request, course_id):
        course = self._load(course_id)
        topics = course.topic_set.all()

        context = self._make_context(course)
        context['topics'] = topics
        return render(request, self.template_name, context)


class CourseProblemsTopicView(BaseCourseView):
    tab = 'problems'
    template_name = 'courses/problems_list.html'

    def get(self, request, course_id, topic_id):
        course = self._load(course_id)
        topic = course.topic_set.filter(id=topic_id).first()
        if topic is None:
            return redirect('courses:course_problems', course_id=course_id)

        problems = topic.list_problems()

        context = self._make_context(course)
        topics = course.topic_set.all()
        context['topics'] = topics
        context['active_topic'] = topic
        context['problems'] = problems
        return render(request, self.template_name, context)


def _locate_in_list(lst, x):
    try:
        pos = lst.index(x)
    except ValueError:
        return None
    length = len(lst)
    return ((pos + length - 1) % length, pos, (pos + 1) % length)


class CourseProblemsTopicProblemView(BaseCourseView, ProblemStatementMixin):
    tab = 'problems'
    template_name = 'courses/problems_statement.html'

    def get(self, request, course_id, topic_id, problem_id, filename):
        course = self._load(course_id)
        topic = self._load_topic(course, topic_id)
        problem = self._load_problem_from_topic(course, topic, problem_id)

        if self.is_aux_file(filename):
            return self.serve_aux_file(request, problem_id, filename)

        if topic.problem_folder is not None:
            problem_ids = topic.problem_folder.problem_set.order_by('number', 'subnumber').values_list('id', flat=True)
            problem_ids = list(problem_ids)  # evaluate the queryset
            problem_id = int(problem_id)  # save because of regexp in urls.py

            positions = _locate_in_list(problem_ids, problem_id)
            if positions is not None:
                context = self._make_context(course)
                prev, cur, next = positions

                context['prev_next'] = True
                context['prev_problem_id'] = problem_ids[prev]
                context['cur_position'] = cur + 1  # 1-based
                context['total_positions'] = len(problem_ids)
                context['next_problem_id'] = problem_ids[next]
                context['statement'] = self.make_statement(problem)

                context['topics'] = course.topic_set.all()
                context['active_topic'] = topic
                return render(request, self.template_name, context)

        # fallback
        return redirect('courses:course_problems', course_id=course_id)


AssignmentDataRepresentation = namedtuple('AssignmentDataRepresentation', 'topics extra_form')
TopicRepresentation = namedtuple('TopicRepresentation', 'topic_id name slots')
SlotRepresentation = namedtuple('SlotRepresentation', 'slot_id form is_penalty extra_requirements')


def create_assignment_form(membership, topic, post_data, slot=None, assignment=None):
    prefix = ''  # form prefix to distinguish forms on page
    if slot is not None:
        prefix = 'm{0}t{1}s{2}'.format(membership.id, topic.id, slot.id)
    elif assignment is not None:
        prefix = 'm{0}t{1}a{2}'.format(membership.id, topic.id, assignment.id)
    else:
        prefix = 'm{0}t{1}new'.format(membership.id, topic.id)

    form = ProblemAssignmentForm(data=post_data, instance=assignment, prefix=prefix)

    # Prepare for form validation
    form.fields['problem'].queryset = topic.list_problems()

    widget = form.fields['problem'].widget
    widget.attrs.update({'data-topic': topic.id})  # to use from JS

    form.fields['criteria'].queryset = topic.criteria

    return form


def prepare_assignment(course, membership, new_penalty_topic=None, post_data=None):
    topic_reprs = []
    topics = course.topic_set.all()
    for topic in topics:
        slot_reprs = []

        for slot in topic.slot_set.all():
            assignment = Assignment.objects.filter(membership=membership, topic=topic, slot=slot).first()
            form = create_assignment_form(
                membership=membership,
                topic=topic,
                post_data=post_data,
                slot=slot,
                assignment=assignment,
            )
            extra_requirements = (assignment and assignment.extra_requirements) or ''
            slot_reprs.append(SlotRepresentation(slot.id, form, False, extra_requirements))

        penalty_assignments = Assignment.objects.filter(membership=membership, topic=topic, slot=None)
        for assignment in penalty_assignments:
            form = create_assignment_form(
                membership=membership,
                topic=topic,
                post_data=post_data,
                assignment=assignment,
            )
            slot_reprs.append(SlotRepresentation(None, form, True, assignment.extra_requirements))

        if new_penalty_topic == topic.id:
            form = create_assignment_form(
                membership=membership,
                topic=topic,
                post_data=post_data,
            )
            slot_reprs.append(SlotRepresentation(None, form, True, ''))

        topic_reprs.append(TopicRepresentation(topic.id, topic.name, slot_reprs))

    extra_form = AddExtraProblemSlotForm()
    extra_form.fields['penaltytopic'].queryset = topics
    return AssignmentDataRepresentation(topic_reprs, extra_form)


class CourseAssignView(BaseCourseView):
    tab = 'assign'
    template_name = 'courses/assign.html'

    def _extract_new_penalty_topic(self, request):
        value = request.GET.get('penaltytopic')
        return int(value) if value is not None else None

    def get(self, request, course_id, membership_id):
        course = self._load(course_id)
        membership = get_object_or_404(Membership, id=membership_id, course=course)

        ass = prepare_assignment(course, membership, self._extract_new_penalty_topic(request))

        context = self._make_context(course)
        context['data'] = ass
        return render(request, self.template_name, context)

    def post(self, request, course_id, membership_id):
        course = self._load(course_id)
        membership = get_object_or_404(Membership, id=membership_id, course=course)

        adr = prepare_assignment(course, membership, self._extract_new_penalty_topic(request), post_data=request.POST)

        all_valid = True

        for topic in adr.topics:
            for slot in topic.slots:
                if not slot.form.is_valid():
                    all_valid = False

        if all_valid:
            with transaction.atomic():
                for topic in adr.topics:
                    for slot in topic.slots:
                        form = slot.form
                        assignment = form.save(commit=False)
                        assignment.membership = membership
                        assignment.topic_id = topic.topic_id
                        assignment.slot_id = slot.slot_id
                        assignment.save()
                        form.save_m2m()

                        if slot.is_penalty and assignment.problem is None:
                            assignment.delete()

            #messages.add_message(request, messages.INFO, 'Hello world.')
            return redirect('courses:course_assignment', course_id=course_id, membership_id=membership_id)

        context = self._make_context(course)
        context['data'] = adr
        return render(request, self.template_name, context)


class CourseListView(generic.ListView):
    model = Course


class CourseCreateView(generic.CreateView):
    model = Course
    fields = ['name']

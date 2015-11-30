# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render, render_to_response, redirect
from django.views import generic
from django.http import HttpResponseRedirect, Http404
from .models import Course, Topic
from .forms import TopicForm, PropertiesForm, CompilersForm
from django.core.urlresolvers import reverse
from django.forms.models import model_to_dict
from proglangs.models import Compiler
from django.db import transaction
from problems.views import ProblemStatementMixin
from problems.models import Problem
from collections import namedtuple

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

        topics = course.topic_set.all().prefetch_related('slot_set')

        header = []
        for topic in topics:
            header.append((topic.name, topic.slot_set.count()))

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

Activity = namedtuple('Activity', 'name weight')
SheetRow = namedtuple('SheetRow', 'user main_activity_scores final_score extra_activity_scores')


class CourseSheetView(BaseCourseView):
    tab = 'sheet'
    template_name = 'courses/sheet.html'

    def get(self, request, course_id):
        course = self._load(course_id)
        rnd = random.Random(1)

        main_activities = (
            Activity(u'Инд. задания', 0.5),
            Activity(u'Контр. раб. 1', 0.3),
            Activity(u'Промеж. тест.', 0.1),
            Activity(u'Итогов. тест.', 0.1),
        )

        extra_activities = (
            Activity(u'Контр. работа №2 AVL-деревья', None),
            Activity(u'Домашнее задание', None),
        )

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
        context = self._make_context(course)
        return render(request, self.template_name, context)


class CourseSettingsSubgroupsView(CourseSettingsView):
    subtab = 'subgroups'
    template_name = 'courses/settings_subgroups.html'

    def get(self, request, course_id):
        course = self._load(course_id)
        context = self._make_context(course)
        return render(request, self.template_name, context)


class CourseSettingsTopicsView(CourseSettingsView):
    subtab = 'topics'
    template_name = 'courses/settings_topics.html'

    def get(self, request, course_id):
        course = self._load(course_id)
        topics = course.topic_set.all().prefetch_related('slot_set')
        context = self._make_context(course)
        context['topics'] = topics
        return render(request, self.template_name, context)


def _save_topic(form, course):
    with transaction.atomic():
        topic = form.save(commit=False)
        topic.course = course
        topic.save()

        target_num_problems = form.cleaned_data['num_problems']
        slots = topic.slot_set.all()
        if len(slots) < target_num_problems:
            diff = target_num_problems - len(slots)
            for _ in range(diff):
                topic.slot_set.create()
        else:
            for slot in slots[target_num_problems:]:
                slot.delete()


class CourseSettingsTopicsCreateView(CourseSettingsView):
    subtab = 'topics'
    template_name = 'courses/settings_topic.html'

    def get(self, request, course_id):
        course = self._load(course_id)
        form = TopicForm(initial={'num_problems': 1})
        context = self._make_context(course)
        context['form'] = form
        return render(request, self.template_name, context)

    def post(self, request, course_id):
        course = self._load(course_id)
        form = TopicForm(request.POST, initial={'course_id': course_id})
        if form.is_valid():
            _save_topic(form, course)
            return redirect('courses:course_settings_topics', course_id=course_id)

        context = self._make_context(course)
        context['form'] = form
        return render(request, self.template_name, context)


class CourseSettingsTopicsUpdateView(CourseSettingsView):
    subtab = 'topics'
    template_name = 'courses/settings_topic.html'

    def get(self, request, course_id, topic_id):
        course = self._load(course_id)

        topic = get_object_or_404(Topic, pk=topic_id)
        num_problems = topic.slot_set.count()

        form = TopicForm(instance=topic, initial={'num_problems': num_problems})
        context = self._make_context(course)
        context['form'] = form
        return render(request, self.template_name, context)

    def post(self, request, course_id, topic_id):
        course = self._load(course_id)
        topic = self._load_topic(course, topic_id)

        form = TopicForm(request.POST, instance=topic)

        if 'save' in request.POST:
            if form.is_valid():
                _save_topic(form, course)
                return redirect('courses:course_settings_topics', course_id=course_id)

        elif 'delete' in request.POST:
            topic.delete()
            return redirect('courses:course_settings_topics', course_id=course_id)

        context = self._make_context(course)
        context['form'] = form
        return render(request, self.template_name, context)

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

        problems = []
        if topic.problem_folder is not None:
            problems = topic.problem_folder.problem_set.all().order_by('number', 'subnumber')

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

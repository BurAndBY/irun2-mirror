# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.views import generic

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
    def _render(self, request, ctxt):
        ctxt.update({
            'course_name': u'2 курс, 14 группа',
            'active_tab': self.tab
        })
        return render(request, 'courses/{0}.html'.format(self.tab), ctxt)


class ShowCourseInfoView(BaseCourseView):
    tab = 'info'

    def get(self, request, course_id):
        return self._render(request, {})


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


class ShowCourseStandingsView(BaseCourseView):
    tab = 'standings'

    def get(self, request, course_id):
        rnd = random.Random(1)

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

        context = {'results': results}

        return self._render(request, context)


class ShowCourseSubmitView(BaseCourseView):
    tab = 'submit'

    def get(self, request, course_id):
        return self._render(request, {})

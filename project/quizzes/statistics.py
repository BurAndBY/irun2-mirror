from django.db.models import Max, Count
from django.utils.translation import ugettext as _

from .models import QuestionGroup, QuizSession, SessionQuestion
from courses.models import Course

from collections import Counter


def get_statistics(template_pk):
    max_grade = QuizSession.objects \
        .filter(quiz_instance__quiz_template_id=template_pk).aggregate(Max('result'))['result__max']
    if max_grade is None:
        return None
    max_grade = int(max_grade)
    stats = {}
    stats['by-year'] = get_statistics_by_year(template_pk, max_grade)
    stats['by-stud-group'] = get_statistics_by_students_group(template_pk, max_grade)
    stats['by-marks'] = get_statistics_by_mark(template_pk, max_grade)
    stats['by-quest-group'] = get_statistics_by_question_group(template_pk)
    stats['by-time'] = get_statistics_by_time(template_pk)
    return stats


def get_statistics_by_year(template_pk, max_grade):
    marks_by_year = QuizSession.objects.filter(quiz_instance__quiz_template_id=template_pk) \
        .values('result', 'quiz_instance__course__academic_year').annotate(total=Count('result')).order_by('result')
    stats = {'categories': []}
    for mark in marks_by_year:
        if str(mark['quiz_instance__course__academic_year']) not in stats['categories']:
            stats['categories'].append(str(mark['quiz_instance__course__academic_year']))
    stats['series'] = [{'name': str(mark),
                        'data': [0 for year in stats['categories']]}
                       for mark in range(max_grade + 1)]
    for mark in marks_by_year:
        idx = stats['categories'].index(str(mark['quiz_instance__course__academic_year']))
        stats['series'][int(mark['result'])]['data'][idx] = mark['total']
    return stats


def get_statistics_by_students_group(template_pk, max_grade):
    max_year = QuizSession.objects.filter(quiz_instance__quiz_template_id=template_pk) \
        .aggregate(max_year=Max('quiz_instance__course__academic_year'))['max_year']
    courses = Course.objects.filter(quizinstance__quiz_template=template_pk, academic_year=max_year)
    id_courses = {course.id: str(course) for course in courses}
    stats = {'categories': [id_courses[id_course] for id_course in id_courses]}
    stats['series'] = [{'name': str(mark),
                        'data': [0 for course in stats['categories']]}
                       for mark in range(max_grade + 1)]
    marks_by_st = QuizSession.objects \
        .filter(quiz_instance__quiz_template_id=template_pk, quiz_instance__course__academic_year=max_year) \
        .values('result', 'quiz_instance__course').annotate(total=Count('result')).order_by('result')
    for mark in marks_by_st:
        idx = stats['categories'].index(id_courses[mark['quiz_instance__course']])
        stats['series'][int(mark['result'])]['data'][idx] = mark['total']
    return stats


def get_statistics_by_mark(template_pk, max_grade):
    stats = {'data': [[str(i), 0] for i in range(max_grade + 1)]}
    marks_count = QuizSession.objects.filter(quiz_instance__quiz_template_id=template_pk) \
        .values('result').annotate(total=Count('result')).order_by('result')
    for mark_count in marks_count:
        stats['data'][int(mark_count['result'])][1] = mark_count['total']
    return stats


def get_statistics_by_question_group(template_pk):
    def make_query(**kwargs):
        data = SessionQuestion.objects\
            .filter(quiz_session__quiz_instance__quiz_template_id=template_pk)\
            .filter(**kwargs)\
            .values('question__group__name').annotate(total=Count('id'))
        return {item['question__group__name']: item['total'] for item in data}

    correct_cnt = make_query(result_points__gt=.0)
    incorrect_cnt = make_query(result_points=.0)

    names = sorted(set(correct_cnt) | set(incorrect_cnt))
    stats = {
        'categories': names,
        'series': [{
            'name': _('Correct'),
            'data': [correct_cnt[name] for name in names]
        }, {
            'name': _('Incorrect'),
            'data': [incorrect_cnt[name] for name in names]
        }]
    }

    return stats


def get_statistics_by_time(template_pk):
    times = QuizSession.objects\
        .filter(quiz_instance__quiz_template_id=template_pk, is_finished=True)\
        .values_list('start_time', 'finish_time')

    minutes_cnt = Counter({0: 0})
    for start_time, finish_time in times:
        minutes = int((finish_time - start_time).seconds / 60) + 1
        minutes_cnt[minutes] += 1
    data = []
    for key in sorted(minutes_cnt):
        data.append([key, minutes_cnt[key]])
    for i in range(1, len(data)):
        data[i][1] += data[i - 1][1]
    return {'data': data}

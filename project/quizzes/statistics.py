from django.db.models import Max, Count
from django.utils.translation import ugettext as _

from .models import QuestionGroup, QuizSession, SessionQuestion
from courses.models import Course


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
        .aggregate(Max('quiz_instance__course__academic_year'))['quiz_instance__course__academic_year__max']
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
    groups = QuestionGroup.objects.filter(quiztemplate=template_pk)
    id_groups = {group.id: group.name for group in groups}
    stats = {'categories': [id_groups[id_group] for id_group in id_groups]}
    stats['series'] = [{'name': _('Correct'), 'data': [0] * len(stats['categories'])},
                       {'name': _('Incorrect'), 'data': [0] * len(stats['categories'])}]
    points = SessionQuestion.objects.filter(quiz_session__quiz_instance__quiz_template_id=template_pk)\
        .values('result_points', 'question__group__name').annotate(total=Count('result_points')).order_by()
    for point in points:
        idx = 0 if point['result_points'] > 0 else 1
        group_idx = stats['categories'].index(point['question__group__name'])
        stats['series'][idx]['data'][group_idx] += point['total']
    return stats


def get_statistics_by_time(template_pk):
    times = QuizSession.objects.filter(quiz_instance__quiz_template_id=template_pk)\
        .values_list('start_time', 'finish_time')

    minutes_dict = {0: 0}
    for start_time, finish_time in times:
        minutes = int((finish_time - start_time).seconds / 60) + 1
        if minutes in minutes_dict:
            minutes_dict[minutes] += 1
        else:
            minutes_dict[minutes] = 1
    data = []
    for key in sorted(minutes_dict):
        data.append([key, minutes_dict[key]])
    for i in range(len(data)):
        if i == 0:
            continue
        data[i][1] += data[i - 1][1]
    return {'data': data}

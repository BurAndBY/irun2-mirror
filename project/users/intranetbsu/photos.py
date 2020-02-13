# -*- coding: utf-8 -*-

from six.moves import urllib

from .parse_func import parse_intranet_bsu_html

BASE_URL = 'http://intranet.bsu/resurses/Students/Find/'
FAMCS = 3


class Request(object):
    def __init__(self, faculty, first_name, last_name, patronymic):
        self.faculty = faculty
        self.first_name = first_name
        self.last_name = last_name
        self.patronymic = patronymic
        self.include_archive = False
        self.group = ''
        self.admission_year = None


def _create_request_params(request):
    params = {}
    params['IdF'] = str(request.faculty)
    if request.include_archive:
        params['IncludeAchrive'] = '1'

    def add(key, value):
        if value is not None:
            value = value.replace('(EPS)', '').replace('(eps)', '').strip()
            if value:
                params[key] = value.encode('cp1251')
    add('NameF', request.last_name)
    add('NameI', request.first_name)
    add('NameO', request.patronymic)
    return params


def fetch_intranet_students(request):
    rp = _create_request_params(request)
    req = urllib.request.Request(BASE_URL, urllib.parse.urlencode(rp).encode('cp1251'))
    response = urllib.request.urlopen(req)
    html = response.read().decode('cp1251')
    students = parse_intranet_bsu_html(html)

    if request.group:
        students = filter(lambda s: s.group == request.group, students)
    if request.admission_year is not None:
        students = filter(lambda s: s.admission_year == request.admission_year, students)

    return students


def download_photo(request):
    '''
    Returns either JPEG blob or None if no photo was found.
    '''
    students = list(fetch_intranet_students(request))
    if len(students) != 1:
        # ambiguous
        return None

    student = students[0]
    if student.photo is None:
        return None

    blob = urllib.request.urlopen(BASE_URL + student.photo).read()
    if len(blob) < 1024:
        # corrupt photo
        return None

    return blob

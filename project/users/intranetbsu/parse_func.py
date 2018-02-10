# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class Student(object):
    def __init__(self):
        self.full_name = None
        self.course = None
        self.group = None
        self.admission_year = None
        self.graduation_year = None
        self.photo = None


def parse_intranet_bsu_html(page):
    table = page[page.find('<TABLE'):page.find('</TABLE>')]
    start_tr, end_tr = table.find('<TR'), table.find('</TR>')
    students = []
    while start_tr >= 0 and end_tr > 0:
        student = Student()
        tr = table[start_tr:end_tr]
        start_el, end_el = tr.find('<B>') + 3, tr.find('</B>')
        student.full_name = tr[start_el:end_el]
        start_el = tr.find(',&nbsp') - 1
        student.course = int(tr[start_el])
        start_el, end_el = tr.find('</i>', start_el) + 4, tr.find('<BR>', start_el)
        if tr[start_el:end_el]:
            student.group = tr[start_el:end_el]
        start_el = tr.find('год поступления:</i>')
        if start_el >= 0:
            start_el += len('год поступления:</i>')
            student.admission_year = int(tr[start_el:start_el + 4])
            start_el = tr.find('год выпуска: </i>', start_el)
            if start_el >= 0:
                start_el += len('год выпуска: </i>')
                student.graduation_year = int(tr[start_el:start_el + 4])
        start_el = tr.find('src="') + 5
        student.photo = tr[start_el:tr.find('"', start_el)]
        students.append(student)
        start_tr, end_tr = table.find('<TR', end_tr), table.find('</TR>', end_tr + 1)
    return students

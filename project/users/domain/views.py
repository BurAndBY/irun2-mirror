from collections import namedtuple

from django.conf import settings
from django.shortcuts import render
from django.utils.encoding import smart_str
from django.views import generic

from cauth.mixins import AdminMemberRequiredMixin

from .forms import StudentInfoForm


StudentInfo = namedtuple('StudentInfo', ['name', 'values'])


class LdapClient:
    def __init__(self, server, username, password):
        import ldap

        ad = ldap.initialize("ldap://{}".format(server))
        ad.set_option(ldap.OPT_REFERRALS, 0)
        ad.simple_bind_s(username, password)
        self._ad = ad

    def lookup(self, first_name, last_name, faculty, attr):
        import ldap
        from ldap.filter import filter_format

        basedn = 'OU=Студенты,OU={},OU=Факультеты,DC=inet,DC=bsu,DC=by'.format(faculty)
        scope = ldap.SCOPE_ONELEVEL
        filterexp = filter_format('(& (sn=%s) (givenName=%s*))', [last_name, first_name])

        values = []
        for _, attrs in self._ad.search_s(basedn, scope, filterexp, [attr]):
            for value in attrs.get(attr, []):
                if value:
                    values.append(smart_str(value))
        return values


class StudentInfoView(AdminMemberRequiredMixin, generic.FormView):
    form_class = StudentInfoForm
    template_name = 'users/domain/student_info.html'
    result_template_name = 'users/domain/student_info_result.html'

    def form_valid(self, form):
        faculty = form.cleaned_data['faculty']
        attr = form.cleaned_data['attribute']
        names = form.cleaned_data['names'].splitlines()

        students = []
        error = None
        try:
            client = LdapClient(settings.BSU_DC, settings.BSU_USERNAME, settings.BSU_PASSWORD)
            for name in names:
                last_name, first_name = name.split(None, 1)
                values = client.lookup(first_name, last_name, faculty, attr)
                students.append(StudentInfo(name, values))
        except Exception as e:
            error = e

        return render(self.request, self.result_template_name, {
            'students': students,
            'error': error,
        })

# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _


class SolutionAccessLevel(object):
    '''
    Helper class to use in course/contest settings to set up access level of students/contestants.
    '''
    NO_ACCESS = 0
    STATE = 1
    COMPILATION_LOG = 2
    SOURCE_CODE = 3
    TESTING_DETAILS = 4
    TESTING_DETAILS_CHECKER_MESSAGES = 5
    TESTING_DETAILS_TEST_DATA = 6

    FULL = TESTING_DETAILS_TEST_DATA

    CHOICES = (
        (NO_ACCESS, _('no access')),
        (STATE, _('view current solution state')),
        (COMPILATION_LOG, _('view compilation log')),
        (SOURCE_CODE, _('view source code')),
        (TESTING_DETAILS, _('view testing details')),
        (TESTING_DETAILS_CHECKER_MESSAGES, _('view testing details with checker messages')),
        (TESTING_DETAILS_TEST_DATA, _('view testing details and test data')),
    )


class SolutionPermissions(object):
    def __init__(self):
        self.tests_data = True
        self.checker_messages = True
        self.source_code = True
        self.compilation_log = True
        self.results = True

    @staticmethod
    def all():
        return SolutionPermissions()

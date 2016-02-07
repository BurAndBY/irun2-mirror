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
        self.state = False
        self.compilation_log = False
        self.source_code = False
        self.results = False
        self.exit_codes = False
        self.checker_messages = False
        self.tests_data = False

        # special permissions that are not included into the levels above
        self.judgements = False
        self.ip_address = False

    def update(self, level):
        if level >= SolutionAccessLevel.STATE:
            self.state = True

        if level >= SolutionAccessLevel.COMPILATION_LOG:
            self.compilation_log = True

        if level >= SolutionAccessLevel.SOURCE_CODE:
            self.source_code = True

        if level >= SolutionAccessLevel.TESTING_DETAILS:
            self.results = True

        if level >= SolutionAccessLevel.TESTING_DETAILS_CHECKER_MESSAGES:
            self.exit_codes = True
            self.checker_messages = True

        if level >= SolutionAccessLevel.TESTING_DETAILS_TEST_DATA:
            self.tests_data = True

    def set_all(self):
        self.update(SolutionAccessLevel.FULL)
        self.judgements = True
        self.ip_address = True

    @staticmethod
    def all():
        permissions = SolutionPermissions()
        permissions.set_all()
        return permissions

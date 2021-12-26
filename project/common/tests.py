# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from django.test import TestCase

from common.templatetags.irunner_time import irunner_timedelta_hms, irunner_timedelta_humanized
from common.locales.tests import *  # noqa
from common.pylightex.tests import *  # noqa


class TimeTagsTests(TestCase):
    # NOTE: \xa0 avoids wrapping between value and unit

    def test_timedelta_0(self):
        dt = datetime.timedelta(seconds=0)
        self.assertEqual(irunner_timedelta_hms(dt), '0:00:00')
        self.assertEqual(irunner_timedelta_humanized(dt), '0\xa0секунд')

    def test_timedelta_1(self):
        dt = datetime.timedelta(minutes=1, seconds=2)
        self.assertEqual(irunner_timedelta_hms(dt), '0:01:02')
        self.assertEqual(irunner_timedelta_humanized(dt), '1\xa0минута 2\xa0секунды')

    def test_timedelta_2(self):
        dt = datetime.timedelta(hours=1, minutes=2, seconds=3)
        self.assertEqual(irunner_timedelta_hms(dt), '1:02:03')
        self.assertEqual(irunner_timedelta_humanized(dt), '1\xa0час 2\xa0минуты')

    def test_timedelta_3(self):
        dt = datetime.timedelta(days=7, hours=23, minutes=59, seconds=59)
        self.assertEqual(irunner_timedelta_hms(dt), '7 дней, 23:59:59')
        self.assertEqual(irunner_timedelta_humanized(dt), '7\xa0дней 23\xa0часа')

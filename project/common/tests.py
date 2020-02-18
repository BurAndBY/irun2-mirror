# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from django.test import TestCase

from common.enum import Enum
from common.templatetags.irunner_time import irunner_timedelta_hms, irunner_timedelta_humanized
from common.pylightex.tests import *  # noqa


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


class ExtendedColor(Color):
    BLACK = 0
    COMPOSITE_NAME = -1


class EnumTests(TestCase):
    def test_basic(self):
        self.assertEqual(Color.RED, 1)
        self.assertEqual(Color.GREEN, 2)
        self.assertEqual(Color.BLUE, Color['BLUE'])
        self.assertEqual(Color.value2key(3), 'BLUE')

        with self.assertRaises(AttributeError):
            Color.BLACK

    def test_get(self):
        self.assertEqual(Color.get('GREEN'), 2)
        self.assertEqual(Color.get('BLUE', 100500), 3)
        self.assertIsNone(Color.get('UNKNOWN'))
        self.assertEqual(Color.get('UNKNOWN', 42), 42)

        with self.assertRaises(TypeError):
            self.assertIsNone(Color.get(None))

        with self.assertRaises(TypeError):
            self.assertIsNone(Color.get(1))

    def test_getitem(self):
        self.assertEqual(Color['GREEN'], 2)

        with self.assertRaises(KeyError):
            Color['UNKNOWN']

    def test_strings(self):
        self.assertEqual(Color.value2key(1), 'RED')
        self.assertEqual(Color.value2key(2), 'GREEN')

        with self.assertRaises(ValueError):
            Color.value2key(100500)

    def test_inheritance(self):
        self.assertEqual(ExtendedColor.RED, 1)
        self.assertEqual(ExtendedColor.BLACK, 0)
        self.assertEqual(ExtendedColor['COMPOSITE_NAME'], -1)
        self.assertEqual(ExtendedColor.value2key(-1), 'COMPOSITE_NAME')

    def test_iterate(self):
        expected_ks = set(['RED', 'GREEN', 'BLUE'])
        expected_kvs = set([('RED', 1), ('GREEN', 2), ('BLUE', 3)])

        self.assertEqual(set(Color), expected_ks)
        self.assertEqual(set(Color.iteritems()), expected_kvs)

        ks = set()
        for k in Color:
            ks.add(k)
        self.assertEqual(expected_ks, ks)

        kvs = set()
        for k, v in Color.iteritems():
            kvs.add((k, v))
        self.assertEqual(expected_kvs, kvs)


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

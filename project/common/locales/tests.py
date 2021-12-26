# -*- coding: utf-8 -*-

from django.test import TestCase

from common.locales.best import find_best_value


class FindBestLocaleTests(TestCase):
    def test_smoke(self):
        i18n_str = {
            'en': 'Hello',
            'ru': 'Привет',
        }
        self.assertEqual(find_best_value(i18n_str.items(), 'en'), 'Hello')
        self.assertEqual(find_best_value(i18n_str.items(), 'ru'), 'Привет')
        self.assertEqual(find_best_value(i18n_str.items(), 'lt'), 'Hello')

        i18n_str = {}
        self.assertEqual(find_best_value(i18n_str.items(), 'en'), '')

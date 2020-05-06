from django.test import TestCase

from contests.services import make_letter


class ContestTests(TestCase):
    def test_make_letter(self):
        self.assertEqual(make_letter(0), 'A')
        self.assertEqual(make_letter(1), 'B')

        self.assertEqual(make_letter(25), 'Z')
        self.assertEqual(make_letter(26), 'AA')
        self.assertEqual(make_letter(27), 'AB')

        self.assertEqual(make_letter(51), 'AZ')
        self.assertEqual(make_letter(52), 'BA')

        self.assertEqual(make_letter(675), 'YZ')
        self.assertEqual(make_letter(676), 'ZA')
        self.assertEqual(make_letter(677), 'ZB')

        self.assertEqual(make_letter(701), 'ZZ')
        self.assertEqual(make_letter(702), 'AAA')

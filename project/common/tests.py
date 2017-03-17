from django.test import TestCase

from common.enum import Enum
from common.katex import parse_tex_math, Portion, PortionMode

PM = PortionMode


class KaTeXMathTests(TestCase):
    def test_no_math(self):
        self.assertEqual(parse_tex_math(''), [])
        self.assertEqual(parse_tex_math(' '), [Portion(' ', PM.TEXT)])
        self.assertEqual(parse_tex_math('abacaba'), [Portion('abacaba', PM.TEXT)])
        self.assertEqual(parse_tex_math('\\$aba\\$aba'), [Portion('$aba$aba', PM.TEXT)])
        self.assertEqual(parse_tex_math('100\\$'), [Portion('100$', PM.TEXT)])
        self.assertEqual(parse_tex_math('1000\\$\\$'), [Portion('1000$$', PM.TEXT)])
        self.assertEqual(parse_tex_math('\\$\\$\\$a'), [Portion('$$$a', PM.TEXT)])

    def test_inline_math(self):
        self.assertEqual(parse_tex_math('$x$'), [Portion('x', PM.INLINE_MATH)])
        self.assertEqual(parse_tex_math('$x$$y$'), [Portion('x', PM.INLINE_MATH), Portion('y', PM.INLINE_MATH)])
        self.assertEqual(parse_tex_math(' $x$'), [Portion(' ', PM.TEXT), Portion('x', PM.INLINE_MATH)])
        self.assertEqual(parse_tex_math('$x$ '), [Portion('x', PM.INLINE_MATH), Portion(' ', PM.TEXT)])
        self.assertEqual(parse_tex_math('$x$ $y+z$'), [Portion('x', PM.INLINE_MATH), Portion(' ', PM.TEXT), Portion('y+z', PM.INLINE_MATH)])
        self.assertEqual(parse_tex_math('$x\\$y$'), [Portion('x$y', PM.INLINE_MATH)])
        self.assertEqual(parse_tex_math('\\$$xy\\$$\\$'), [Portion('$', PM.TEXT), Portion('xy$', PM.INLINE_MATH), Portion('$', PM.TEXT)])

    def test_display_math(self):
        self.assertEqual(parse_tex_math('$$x$$'), [Portion('x', PM.DISPLAYED_MATH)])
        self.assertEqual(parse_tex_math('$$x\\$$$'), [Portion('x$', PM.DISPLAYED_MATH)])
        self.assertEqual(parse_tex_math('$$$$'), [])
        self.assertEqual(parse_tex_math('$$x$$$y$'), [Portion('x', PM.DISPLAYED_MATH), Portion('y', PM.INLINE_MATH)])
        self.assertEqual(parse_tex_math('$x$$$y$$'), [Portion('x', PM.INLINE_MATH), Portion('y', PM.DISPLAYED_MATH)])
        self.assertEqual(parse_tex_math('$$x$$$$y$$'), [Portion('x', PM.DISPLAYED_MATH), Portion('y', PM.DISPLAYED_MATH)])

    def test_errors(self):
        self.assertEqual(parse_tex_math('$x'), [Portion('x', PM.INLINE_MATH)])
        self.assertEqual(parse_tex_math('$$x'), [Portion('x', PM.DISPLAYED_MATH)])
        self.assertEqual(parse_tex_math('$$x$y$$'), [Portion('x', PM.DISPLAYED_MATH), Portion('y', PM.TEXT)])


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

from django.test import TestCase

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

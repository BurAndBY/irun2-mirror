# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest
import logging

from .convert import tex2html as tex2html_general
from .highlight import do_highlight


def tex2html(tex, inline=False):
    return tex2html_general(tex, inline=inline, pygmentize=False, wrap=False)


class TestBasic(unittest.TestCase):
    def test_paragraph(self):
        self.assertEqual(tex2html(''), '')
        self.assertEqual(tex2html('a'), '<div class="paragraph">a</div>')
        self.assertEqual(tex2html('a\nb'), '<div class="paragraph">a\nb</div>')
        self.assertEqual(tex2html('a\n\nb'), '<div class="paragraph">a</div><div class="paragraph">b</div>')
        self.assertEqual(tex2html('a\n\n\nb'), '<div class="paragraph">a</div><div class="paragraph">b</div>')

        self.assertEqual(tex2html('\na'), '<div class="paragraph">\na</div>')
        self.assertEqual(tex2html('\n\na'), '<div class="paragraph">a</div>')
        self.assertEqual(tex2html('\n\n\na'), '<div class="paragraph">a</div>')

        self.assertEqual(tex2html('a\n'), '<div class="paragraph">a\n</div>')
        self.assertEqual(tex2html('a\n\n'), '<div class="paragraph">a</div>')
        self.assertEqual(tex2html('a\n\n\n'), '<div class="paragraph">a</div>')

    def test_comments(self):
        self.assertEqual(tex2html('a%bcd'), '<div class="paragraph">a</div>')
        self.assertEqual(tex2html('a\\%bcd'), '<div class="paragraph">a%bcd</div>')
        self.assertEqual(tex2html('% just a comment'), '<div class="paragraph"></div>')
        self.assertEqual(tex2html('% just a comment\n\n'), '<div class="paragraph"></div>')

    def test_html_escaping(self):
        self.assertEqual(tex2html('x < y > z', inline=True), 'x &lt; y &gt; z')

    def test_special_characters(self):
        self.assertEqual(tex2html('\\\\ [ ] \\{ \\}', inline=True), '\\ [ ] { }')
        self.assertEqual(tex2html('_', inline=True), '_')

    def test_spaces(self):
        self.assertEqual(tex2html('a~b', inline=True), 'a\u00A0b')

    def test_quotes(self):
        self.assertEqual(tex2html('<<a>>', inline=True), '«a»')
        self.assertEqual(tex2html('<a>', inline=True), '&lt;a&gt;')

    def test_dashes(self):
        self.assertEqual(tex2html('a--b', inline=True), 'a–b')
        self.assertEqual(tex2html('a---b', inline=True), 'a—b')
        self.assertEqual(tex2html('a-{}-b', inline=True), 'a--b')
        self.assertEqual(tex2html('a-{}--b', inline=True), 'a-–b')

    def test_text_styles(self):
        self.assertEqual(tex2html('\\texttt{}', inline=True), '<span class="monospace"></span>')
        self.assertEqual(tex2html('\\texttt{a}', inline=True), '<span class="monospace">a</span>')
        self.assertEqual(tex2html('\\textit{aba caba}', inline=True), '<i>aba caba</i>')
        self.assertEqual(tex2html('This text is \\textbf{\\{BOLD\\}}', inline=True), 'This text is <b>{BOLD}</b>')
        self.assertEqual(tex2html('\\texttt{\\textit{b}}', inline=True), '<span class="monospace"><i>b</i></span>')
        self.assertEqual(tex2html('\\texttt{\\textit{a}b\\textit{c}}', inline=True), '<span class="monospace"><i>a</i>b<i>c</i></span>')
        self.assertEqual(tex2html('\\emph{note}', inline=True), '<em>note</em>')


class TestMath(unittest.TestCase):
    def test_inline(self):
        self.assertEqual(tex2html('$x$'), '<div class="paragraph"><span class="math">x</span></div>')
        self.assertEqual(tex2html('$x_i$'), '<div class="paragraph"><span class="math">x_i</span></div>')
        self.assertEqual(tex2html('$\\sqrt{x^2}$'), '<div class="paragraph"><span class="math">\\sqrt{x^2}</span></div>')
        self.assertEqual(tex2html('$x^2\n$'), '<div class="paragraph"><span class="math">x^2\n</span></div>')
        # TODO: '$x$$y$'
        # self.assertEqual(tex2html('$x$$y$', inline=True), '<span class="math">x</span><span class="math">y</span>')
        self.assertEqual(tex2html('$x$ $y$', inline=True), '<span class="math">x</span> <span class="math">y</span>')

    def test_display(self):
        self.assertEqual(tex2html('$$x$$'), '<div class="paragraph"><div class="math">x</div></div>')
        self.assertEqual(tex2html('$$x$$$$y$$'), '<div class="paragraph"><div class="math">x</div><div class="math">y</div></div>')

    def test_math_escaping_dollars(self):
        self.assertEqual(tex2html(r'$100\$$', inline=True), r'<span class="math">100\$</span>')
        self.assertEqual(tex2html(r'$x\$y$', inline=True), r'<span class="math">x\$y</span>')
        self.assertEqual(tex2html(r'$1\\2$', inline=True), r'<span class="math">1\\2</span>')
        self.assertEqual(tex2html(r'$x\\$', inline=True), r'<span class="math">x\\</span>')
        self.assertEqual(tex2html(r'$\$\$\$$', inline=True), r'<span class="math">\$\$\$</span>')
        self.assertEqual(tex2html(r'\$$xy\$$\$', inline=True), r'$<span class="math">xy\$</span>$')

    def test_math_escaping_html(self):
        self.assertEqual(tex2html('$x < y > z$', inline=True), '<span class="math">x &lt; y &gt; z</span>')
        self.assertEqual(tex2html('$x \\& y$', inline=True), '<span class="math">x \\&amp; y</span>')

    def test_no_math(self):
        self.assertEqual(tex2html('\\$aba\\$aba', inline=True), '$aba$aba')
        self.assertEqual(tex2html('100\\$', inline=True), '100$')
        self.assertEqual(tex2html('1000\\$\\$', inline=True), '1000$$')
        self.assertEqual(tex2html('\\$\\$\\$a', inline=True), '$$$a')


class TestVerbatim(unittest.TestCase):
    def test_verb(self):
        self.assertEqual(tex2html('\\verb{hello}'), '<div class="paragraph"><span class="verbatim">hello</span></div>')
        self.assertEqual(tex2html('\\verb{{hello}}'), '<div class="paragraph"><span class="verbatim">{hello}</span></div>')
        self.assertEqual(tex2html('\\verb{a{b}}'), '<div class="paragraph"><span class="verbatim">a{b}</span></div>')
        self.assertEqual(tex2html('\\verb{{a}b}'), '<div class="paragraph"><span class="verbatim">{a}b</span></div>')
        self.assertEqual(tex2html('\\verb{{a}{b}}'), '<div class="paragraph"><span class="verbatim">{a}{b}</span></div>')
        self.assertEqual(tex2html('\\verb{{{{a}}b}{cd}}'), '<div class="paragraph"><span class="verbatim">{{{a}}b}{cd}</span></div>')
        self.assertEqual(tex2html('\\verb{\\verb{ }}'), '<div class="paragraph"><span class="verbatim">\\verb{ }</span></div>')
        self.assertEqual(tex2html('\\verb{\\verb{}}'), '<div class="paragraph"><span class="verbatim">\\verb{}</span></div>')

    def test_verb_traditional(self):
        self.assertEqual(tex2html('\\verb|a|', inline=True), '<span class="verbatim">a</span>')
        self.assertEqual(tex2html('\\verb!a|b!', inline=True), '<span class="verbatim">a|b</span>')
        self.assertEqual(tex2html('\\verb|}{|', inline=True), '<span class="verbatim">}{</span>')
        self.assertEqual(tex2html('\\verb|<  >|', inline=True), '<span class="verbatim">&lt;  &gt;</span>')

    def test_verbatim_env(self):
        self.assertEqual(tex2html('\\begin{verbatim}#include <iostream>\\end{verbatim}'),
                         '<div class="paragraph"><div class="verbatim">#include &lt;iostream&gt;</div></div>')

    def test_mintinline(self):
        self.assertEqual(tex2html('\\mintinline{bash}{VAR1=${VAR2}}', inline=True), '<span class="verbatim">VAR1=${VAR2}</span>')

    def test_minted_env(self):
        self.assertEqual(tex2html('\\begin{minted}{bash}\n#!/bin/bash\n\necho "Hello, world!"\n\\end{minted}'),
                         '<div class="paragraph"><div class="verbatim">#!/bin/bash\n\necho "Hello, world!"\n</div></div>')


class TestPygments(unittest.TestCase):
    def test_inline_false(self):
        self.assertEqual(do_highlight('int x;\nfoo();', 'cpp'),
                         '<span class="kt">int</span> '
                         '<span class="n">x</span>'
                         '<span class="p">;</span>\n'
                         '<span class="n">foo</span>'
                         '<span class="p">();</span>\n')

    def test_inline_true(self):
        self.assertEqual(do_highlight('int x', 'cpp'),
                         '<span class="kt">int</span> '
                         '<span class="n">x</span>\n')

    def test_bad_lang(self):
        self.assertEqual(do_highlight('Foo<42>()', 'doesnotexist'),
                         'Foo&lt;42&gt;()\n')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()

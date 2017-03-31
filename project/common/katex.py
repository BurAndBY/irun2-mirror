from __future__ import unicode_literals

import re
from collections import namedtuple

from django.utils.html import escape, format_html, mark_safe


class PortionMode(object):
    TEXT = 1
    INLINE_MATH = 2
    DISPLAYED_MATH = 3

Portion = namedtuple('Portion', 'data mode')


class Parser(object):
    ONE_DOLLAR = 1
    TWO_DOLLARS = 2

    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.endpos = len(data)

    def _seek(self, expect):
        result = ''
        while True:
            npos = self.data.find('$', self.pos)
            if npos == -1:
                result += self.data[self.pos:]
                self.pos = self.endpos
                return (result, None)

            assert self.data[npos] == '$'

            if npos > self.pos and self.data[npos - 1] == '\\':
                result += self.data[self.pos:npos - 1]
                result += self.data[npos]
                self.pos = npos + 1
                continue

            if (expect is None) or (expect == Parser.TWO_DOLLARS):
                if (npos + 1 < self.endpos) and self.data[npos + 1] == '$':
                    result += self.data[self.pos:npos]
                    self.pos = npos + 2
                    return (result, Parser.TWO_DOLLARS)

            result += self.data[self.pos:npos]
            self.pos = npos + 1
            return (result, Parser.ONE_DOLLAR)

    def run(self):
        ans = []
        mode = PortionMode.TEXT

        while self.pos < self.endpos:
            expect = None
            if mode == PortionMode.INLINE_MATH:
                expect = Parser.ONE_DOLLAR
            if mode == PortionMode.DISPLAYED_MATH:
                expect = Parser.TWO_DOLLARS

            substr, got = self._seek(expect)
            if substr:
                ans.append(Portion(substr, mode))

            if expect is not None:
                if expect == got:
                    mode = PortionMode.TEXT
                else:
                    # error
                    mode = PortionMode.TEXT
                    pass
            else:
                if got == Parser.ONE_DOLLAR:
                    mode = PortionMode.INLINE_MATH
                if got == Parser.TWO_DOLLARS:
                    mode = PortionMode.DISPLAYED_MATH
        return ans


def parse_tex_math(s):
    return Parser(s).run()


def _process_text(s):
    tokens = re.split('\n{2,}', s)
    return '<br>'.join(escape(t) for t in tokens)


def tex2html(s):
    portions = parse_tex_math(s)
    tokens = []
    for portion in portions:
        if portion.mode == PortionMode.TEXT:
            tokens.append(_process_text(portion.data))
        elif portion.mode == PortionMode.INLINE_MATH:
            tokens.append(format_html('<span class="ir-katex-inline">{}</span>', portion.data))
        elif portion.mode == PortionMode.DISPLAYED_MATH:
            tokens.append(format_html('<div class="ir-katex-displayed">{}</div>', portion.data))

    return mark_safe(''.join(tokens))

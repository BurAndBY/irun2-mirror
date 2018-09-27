from __future__ import unicode_literals

from collections import namedtuple

from django.utils.html import escape

from common.constants import STDIN, STDOUT

# for strings passed to external library
TEX2HTML_ENCODING = 'utf-8'

IMAGE_PATH = '/fIpZ6d9gT5GYgPFox3cO/'

'''
output contains HTML data
'''
TeXRenderResult = namedtuple('TeXRenderResult', 'output log')


def _render(begin, tex_source, end):
    src = begin + tex_source + end
    try:
        import tex2html
        src = src.encode(TEX2HTML_ENCODING)
        dst, log = tex2html.convert(src)
        dst, log = dst.decode(TEX2HTML_ENCODING, errors='replace'), log.decode(TEX2HTML_ENCODING, errors='replace')
    except ImportError as e:
        dst, log = ('<pre>' + escape(src) + '</pre>'), unicode(e)

    dst = dst.replace(IMAGE_PATH, '')
    return TeXRenderResult(dst, log)


def render_tex_with_header(tex_source, problem):
    begin = '\\begin{problem}{%s}{%s}{%s}{0 seconds}{%s}{}\n' % (
        problem.numbered_full_name_difficulty(),
        problem.input_filename or STDIN,
        problem.output_filename or STDOUT,
        'no memory limit',
    )
    end = '\n\\end{problem}\n'
    return _render(begin, tex_source, end)


def render_tex(tex_source, input_filename=None, output_filename=None):
    begin = '\\begin{rawproblem}{%s}{%s}\n' % (
        input_filename or STDIN,
        output_filename or STDOUT,
    )
    end = '\n\\end{rawproblem}\n'
    return _render(begin, tex_source, end)

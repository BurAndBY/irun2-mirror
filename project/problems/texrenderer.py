import tex2html

# for strings passed to external library
TEX2HTML_ENCODING = 'utf-8'


class TeXRenderer(object):
    IMAGE_PATH = '/fIpZ6d9gT5GYgPFox3cO/'

    def __init__(self):
        self.tex_source = ''
        self.problem_name = ''
        self.memory_limits = None
        self.input_file = None
        self.output_file = None

    @staticmethod
    def create(problem, tex_source):
        renderer = TeXRenderer()
        renderer.problem_name = problem.numbered_full_name()
        renderer.input_file = problem.input_filename
        renderer.output_file = problem.output_filename
        renderer.tex_source = tex_source
        return renderer

    def _render(self):
        begin = u'\\begin{problem}{%s}{%s}{%s}{0 seconds}{%s}{}\n' % (
            self.problem_name,
            self.input_file if self.input_file is not None else 'standart input',
            self.output_file if self.output_file is not None else 'standart output',
            'no memory limit'
        )
        end = u'\n\\end{problem}\n'

        src = (begin + self.tex_source + end).encode(TEX2HTML_ENCODING)
        dst, log = tex2html.convert(src)
        dst, log = dst.decode(TEX2HTML_ENCODING), log.decode(TEX2HTML_ENCODING)

        dst = dst.replace(TeXRenderer.IMAGE_PATH, '')
        return (dst, log)

    def render_inner_html(self):
        dst, _ = self._render()
        return dst

    def render_json(self):
        raise NotImplementedError()

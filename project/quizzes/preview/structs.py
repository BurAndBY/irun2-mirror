class PreviewSource(object):
    def __init__(self, tex, inline):
        self.tex = tex
        self.inline = inline


class PreviewResult(object):
    def __init__(self, html):
        self.html = html

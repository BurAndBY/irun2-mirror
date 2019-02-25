from pygments.formatters import HtmlFormatter

import sys
from os.path import dirname, join, abspath

sys.path.insert(0, abspath(join(dirname(__file__), '..', '..')))


from pylightex import tex2html


def main():
    formatter = HtmlFormatter(style='default')
    styles = formatter.get_style_defs('.pylightex .verbatim')

    with open('input.tex', 'rb') as fd:
        tex = fd.read().decode('utf-8')

    result = tex2html(tex)

    with open('template.html', 'rb') as fd:
        template = fd.read().decode('utf-8')

    page = template
    page = page.replace('$BODY', result)
    page = page.replace('$STYLE', styles)

    with open('output.html', 'wb') as fd:
        fd.write(page.encode('utf-8'))


if __name__ == '__main__':
    main()

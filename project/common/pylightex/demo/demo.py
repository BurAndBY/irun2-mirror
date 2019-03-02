from __future__ import unicode_literals
from __future__ import print_function

from pygments.formatters import HtmlFormatter

import argparse
import sys
import os.path

SCRIPT_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..')))


from pylightex import tex2html


def read_file(path):
    with open(path, 'rb') as fd:
        return fd.read().decode('utf-8')


def write_file(path, content):
    with open(path, 'wb') as fd:
        return fd.write(content.encode('utf-8'))


def process(path, template, css):
    print(path, file=sys.stderr)
    tex = read_file(path)
    files = {
        'input': 'input.txt',
        'output': 'output.txt',
    }
    try:
        result = tex2html(tex, olymp_file_names=files, throw=True)
    except Exception as e:
        print(unicode(e), file=sys.stderr)
        return
    page = template
    page = page.replace('$BODY', result)
    page = page.replace('$STYLE', css)
    write_file(path + '.html', page)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='?', default='input.tex')
    args = parser.parse_args()

    template = read_file(os.path.join(SCRIPT_DIR, 'template.html'))
    css = read_file(os.path.join(SCRIPT_DIR, 'pylightex.css'))

    # append pygments styles
    formatter = HtmlFormatter(style='default')
    styles = formatter.get_style_defs('.pylightex .verbatim')
    css += styles

    if os.path.isdir(args.input):
        for dirpath, dirnames, filenames in os.walk(args.input):
            for fn in filenames:
                if fn.endswith('.tex'):
                    process(os.path.join(dirpath, fn), template, css)
    else:
        process(args.input, template, css)


if __name__ == '__main__':
    main()

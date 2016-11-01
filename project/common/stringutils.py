# -*- coding: utf-8 -*-

from __future__ import unicode_literals

ELLIPSIS = '…'


def _cut_line(line, max_line_length):
    if len(line) <= max_line_length:
        return line
    last_space = line.rfind(' ', 0, max_line_length)
    if last_space != -1 and last_space >= max_line_length // 2:
        return line[:last_space] + ELLIPSIS
    else:
        return line[:(max_line_length-3)] + ELLIPSIS


def cut_text_block(text, max_lines=None, max_line_length=None):
    '''
    returns: a tuple (modified, result)
    '''

    if (max_lines is None) and (max_line_length is None):
        return (False, text)

    lines = text.splitlines(False)
    modified = False

    if (max_lines is not None) and (len(lines) > max_lines):
        keep_lines = max(0, max_lines - 1)
        lines = lines[:keep_lines] + [ELLIPSIS]
        modified = True

    if (max_line_length is not None):
        cut_lines = []
        for line in lines:
            cut_line = _cut_line(line, max_line_length)
            if line != cut_line:
                modified = True
            cut_lines.append(cut_line)
        lines = cut_lines

    if modified:
        text = '\n'.join(lines)

    return (modified, text)

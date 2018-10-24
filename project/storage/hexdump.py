from __future__ import unicode_literals

from collections import namedtuple
from six import iterbytes
from six.moves import range
import string

HexLine = namedtuple('HexLine', 'offset hex1 hex2 ascii')

HALF_ROW_LENGTH = 8
ROW_LENGTH = HALF_ROW_LENGTH * 2
DISPLAY_CHARS = string.digits + string.ascii_letters + string.punctuation
FILTER = ''.join(((x if x in DISPLAY_CHARS else '.') for x in map(chr, range(256))))


def hexdump(data):
    lines = []
    for c in range(0, len(data), ROW_LENGTH):
        row = data[c:c+ROW_LENGTH]
        hex_bytes = ['{:02x}'.format(x) for x in iterbytes(row)]
        hex_bytes += ['  '] * (ROW_LENGTH - len(row))  # complete the row

        lines.append(HexLine(
            '{:08x}'.format(c),
            ' '.join(hex_bytes[:HALF_ROW_LENGTH]),
            ' '.join(hex_bytes[HALF_ROW_LENGTH:]),
            ''.join(FILTER[x] for x in iterbytes(row))
        ))
    return lines


def text_hexdump(data):
    return ''.join(
        '{}:  {}  {}  |{}|\n'.format(line.offset, line.hex1, line.hex2, line.ascii)
        for line in hexdump(data)
    )

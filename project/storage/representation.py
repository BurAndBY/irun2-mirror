from __future__ import unicode_literals

import six

from common.stringutils import cut_text_block
from .encodings import try_decode_ascii
from .hexdump import hexdump


class ResourseRepresentation(object):
    IS_BINARY = 1
    IS_COMPLETE = 2
    IS_UTF8 = 4
    HAS_BOM = 8

    def __init__(self, size, flags, text, hexdata):
        self.size = size
        self.flags = flags
        self.text = text
        self.hexdata = hexdata

    def is_binary(self):
        return bool(ResourseRepresentation.IS_BINARY & self.flags)

    def is_complete(self):
        return bool(ResourseRepresentation.IS_COMPLETE & self.flags)

    def is_utf8(self):
        return bool(ResourseRepresentation.IS_UTF8 & self.flags)

    def has_bom(self):
        return bool(ResourseRepresentation.HAS_BOM & self.flags)

    def is_empty(self):
        return self.size == 0

    @property
    def complete_text(self):
        return self.text if self.is_complete() else None

    @property
    def editable_text(self):
        return self.text if (self.is_complete() and self.is_utf8() and not self.has_bom()) else None


def _is_control_char(code):
    return (code < 9) or (13 < code < 32) or (code == 127)


def _is_binary(blob):
    if isinstance(blob, six.binary_type):
        return any(_is_control_char(code) for code in six.iterbytes(blob))
    if isinstance(blob, six.text_type):
        return any(_is_control_char(ord(c)) for c in blob)
    raise TypeError('unsupported argument type: {}'.format(type(blob)))


UTF8_BOM = b'\xEF\xBB\xBF'
UTF16_BOM = b'\xFF\xFE'


def _cut_utf_bom(blob, bom):
    return blob[len(bom):] if blob.startswith(bom) else None


def _try_decode_utf(encoding, blob, is_complete):
    try:
        return blob.decode(encoding)
    except UnicodeDecodeError:
        pass

    if not is_complete:
        # try to cut the last char: it may be broken
        try:
            return blob[:-1].decode(encoding)
        except UnicodeDecodeError:
            pass

    return None


def _decode_plain_text(blob, is_complete):
    '''
    Returns (text, flags) pair.
    '''

    # try UTF-16 (only with BOM)
    no_bom_blob = _cut_utf_bom(blob, UTF16_BOM)
    if no_bom_blob is not None:
        text = _try_decode_utf('utf-16', no_bom_blob, is_complete)
        if text is not None:
            if _is_binary(text):
                return (None, ResourseRepresentation.IS_BINARY)
            else:
                return (text, ResourseRepresentation.HAS_BOM)

    # real binary files
    if _is_binary(blob):
        return (None, ResourseRepresentation.IS_BINARY)

    # try UTF-8
    no_bom_blob = _cut_utf_bom(blob, UTF8_BOM)
    if no_bom_blob is not None:
        text = _try_decode_utf('utf-8', no_bom_blob, is_complete)
        if text is not None:
            return (text, ResourseRepresentation.IS_UTF8 | ResourseRepresentation.HAS_BOM)

    # most common case
    text = _try_decode_utf('utf-8', blob, is_complete)
    if text is not None:
        return (text, ResourseRepresentation.IS_UTF8)

    text = try_decode_ascii(blob)
    return (text, 0)


def represent_blob(blob, full_size=None, max_lines=None, max_line_length=None):
    '''
    Returns ResourseRepresentation for the given BLOB.
    '''

    if full_size is None:
        full_size = len(blob)
    assert isinstance(blob, six.binary_type)
    assert len(blob) <= full_size
    is_complete = len(blob) == full_size

    text, flags = _decode_plain_text(blob, is_complete)
    hexdata = None

    if text is not None:
        modified, text = cut_text_block(text, max_lines, max_line_length)
        if modified:
            is_complete = False

    if (flags & ResourseRepresentation.IS_BINARY) != 0:
        hexdata = hexdump(blob)
        if (max_lines is not None) and (len(hexdata) > max_lines):
            hexdata = hexdata[:max_lines]
            is_complete = False

    if is_complete:
        flags |= ResourseRepresentation.IS_COMPLETE

    return ResourseRepresentation(full_size, flags, text, hexdata)

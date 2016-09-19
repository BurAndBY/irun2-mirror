import chardet

CP866 = 'IBM866'
CP1251 = 'Windows-1251'


def try_decode_ascii(s):
    '''
    Decodes a string as Windows-1251 (more probably) or CP866.
    If no success, returns None.
    '''

    result = chardet.detect(s)
    encoding = result.get('encoding')
    if encoding not in (CP866, CP1251):
        encoding = CP1251

    try:
        return s.decode(encoding)
    except UnicodeDecodeError:
        pass

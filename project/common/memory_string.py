import re


def parse_memory(s):
    m = re.match(r'^(\d+)(M|m)(B|b)?$', s)
    if m is not None:
        return (2 ** 20) * int(m.group(1))

    m = re.match(r'^(\d+)(K|k)(B|b)?$', s)
    if m is not None:
        return (2 ** 10) * int(m.group(1))

    m = re.match(r'^(\d+)$', s)
    if m is not None:
        return int(m.group(1))

    raise ValueError('Unable to parse memoty amout from {0}'.format(s))

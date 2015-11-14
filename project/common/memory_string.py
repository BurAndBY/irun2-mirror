import re


def parse_memory(s):
    m = re.match(r'^(\d+)(M|m)$', s)
    if m is not None:
        return (2 ** 20) * int(m.group(1))
    raise ValueError('Unable to parse memoty amout from {0}'.format(s))

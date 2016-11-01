MAX_LINES = 320
CHARS_PER_LINE = 80


def _get_printed_lines(s):
    return max((len(s) + CHARS_PER_LINE - 1) // CHARS_PER_LINE, 1)


def check_size_limits(s):
    num_lines = sum((_get_printed_lines(line) for line in s.splitlines()))
    return (num_lines <= MAX_LINES)

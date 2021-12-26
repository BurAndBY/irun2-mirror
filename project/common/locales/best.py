def find_best(locales, needed, extract=lambda v: v):
    for loc in locales:
        if extract(loc) == needed:
            return loc
    for loc in locales:
        if extract(loc) == 'en':
            return loc
    return next(iter(locales))


def find_best_pair(locale_pairs, needed):
    return find_best(locale_pairs, needed, lambda kv: kv[0])


def find_best_value(locale_pairs, needed):
    try:
        return find_best_pair(locale_pairs, needed)[1]
    except StopIteration:
        return ''

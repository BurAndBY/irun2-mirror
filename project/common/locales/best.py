def find_best(locales, needed, extract=lambda v: v):
    for loc in locales:
        if extract(loc) == needed:
            return loc
    for loc in locales:
        if extract(loc) == 'en':
            return loc
    return next(iter(locales))


def find_best_pair(locales, needed):
    return find_best(locales, needed, lambda kv: kv[0])

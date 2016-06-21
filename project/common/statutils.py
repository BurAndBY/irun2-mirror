from collections import namedtuple, Counter

from proglangs.models import get_language_label
from solutions.models import Judgement

from .outcome import Outcome

ProgrammingLanguageBar = namedtuple('ProgrammingLanguageBar', 'language label count percent')


def build_proglangbars(solution_queryset):
    stats = Counter()
    total = 0
    for language in solution_queryset.values_list('compiler__language', flat=True):
        stats[language] += 1
        total += 1

    bars = []
    for language, count in stats.most_common():
        percent = count * 100 // total
        label = get_language_label(language) or language
        bars.append(ProgrammingLanguageBar(language, label, count, percent))

    return bars


OutcomeBar = namedtuple('OutcomeBar', 'outcome name count percent')


def build_outcomebars(solution_queryset):
    stats = Counter()
    total = 0
    for outcome in solution_queryset.\
            filter(best_judgement__status=Judgement.DONE).\
            values_list('best_judgement__outcome', flat=True):
        stats[outcome] += 1
        total += 1

    names = {}
    for outcome, name in Outcome.CHOICES:
        names[outcome] = name

    bars = []
    for outcome, count in stats.most_common():
        percent = count * 100 // total
        bars.append(OutcomeBar(outcome, names.get(outcome, ''), count, percent))
    return bars

from proglangs.models import Compiler

from common.outcome import Outcome
from .models import Judgement

STATE_FILTERS = {
    'waiting': lambda q: q.filter(best_judgement__status=Judgement.WAITING),
    'preparing': lambda q: q.filter(best_judgement__status=Judgement.PREPARING),
    'compiling': lambda q: q.filter(best_judgement__status=Judgement.COMPILING),
    'testing': lambda q: q.filter(best_judgement__status=Judgement.TESTING),
    'finishing': lambda q: q.filter(best_judgement__status=Judgement.FINISHING),
    'done': lambda q: q.filter(best_judgement__status=Judgement.DONE),
    'not-done': lambda q: q.exclude(best_judgement__status=Judgement.DONE),
    'ok': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.ACCEPTED),
    'ce': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.COMPILATION_ERROR),
    'wa': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.WRONG_ANSWER),
    'tle': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.TIME_LIMIT_EXCEEDED),
    'mle': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.MEMORY_LIMIT_EXCEEDED),
    'ile': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.IDLENESS_LIMIT_EXCEEDED),
    'rte': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.RUNTIME_ERROR),
    'pe': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.PRESENTATION_ERROR),
    'sv': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.SECURITY_VIOLATION),
    'cf': lambda q: q.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.CHECK_FAILED),
}


def apply_state_filter(solution_queryset, value):
    state_filter = STATE_FILTERS.get(value)
    if state_filter is not None:
        solution_queryset = state_filter(solution_queryset)
    return solution_queryset


def apply_compiler_filter(solution_queryset, value):
    if value:
        ok = False
        for language, _ in Compiler.LANGUAGE_CHOICES:
            if language == value:
                solution_queryset = solution_queryset.filter(compiler__language=language)
                ok = True
                break
        if not ok:
            solution_queryset = solution_queryset.filter(compiler_id=value)
    return solution_queryset

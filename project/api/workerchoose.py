from collections import namedtuple

from problems.models import ProblemRelatedSourceFile
from solutions.models import Judgement
from proglangs.langlist import ProgrammingLanguage

from api.worker import DefaultWorker, UnixWorker
from api.objectinqueue import JudgementInQueue

ChosenWorker = namedtuple('ChosenWorker', ['db_obj', 'worker'])


def choose_workers(objs):
    judgement_ids = set()

    # we need to iterate them twice
    objs = list(objs)

    for obj in objs:
        if isinstance(obj, JudgementInQueue):
            judgement_ids.add(obj.judgement_id)

    # TODO: XXX find better way
    unix_judgement_ids = set(
        Judgement.objects.
        filter(solution__problem__problemrelatedsourcefile__file_type=ProblemRelatedSourceFile.CHECKER).
        filter(solution__problem__problemrelatedsourcefile__compiler__language=ProgrammingLanguage.PYTHON).
        distinct().values_list('id', flat=True)
    )

    for obj in objs:
        worker = DefaultWorker
        if isinstance(obj, JudgementInQueue):
            if obj.judgement_id in unix_judgement_ids:
                worker = UnixWorker

        yield ChosenWorker(obj, worker)

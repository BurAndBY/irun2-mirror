from common.outcome import Outcome
from solutions.models import Solution
from plagiarism.models import JudgementResult, AggregatedResult
from plagiarism.plagiarismstructs import PlagiarismSubJob, PlagiarismTestingJob
from storage.storage import ResourceId
from django.db import transaction


def _make_job_field(id, res):
    return PlagiarismSubJob(id, res)


def _make_job(solution, solutions):
    return PlagiarismTestingJob(
        _make_job_field(solution['id'], str(solution['resource'])),
        [_make_job_field(_['id'], str(_['resource'])) for _ in solutions])


def get_testing_job():
    solution_to_test = Solution.objects.filter(
        judgement__outcome=Outcome.ACCEPTED,
        aggregatedresult__isnull=True).order_by('-reception_time').first()

    if not solution_to_test:
        return None

    solution = {
        'id': solution_to_test.id,
        'resource': solution_to_test.source_code.resource_id
    }

    solutions_to_compare = Solution.objects.filter(
        judgement__outcome=Outcome.ACCEPTED,
        problem_id=solution_to_test.problem_id,
        reception_time__lt=solution_to_test.reception_time
    ).exclude(author_id=solution_to_test.author_id).distinct()

    solutions = [
        {'id': sol.id, 'resource': sol.source_code.resource_id}
        for sol in solutions_to_compare
    ]

    return _make_job(solution, solutions)


def _create_judgementresult_insert(data):
    vals = [
        AggregatedResult(
            id_id=data['id'],
            relevance=data['plagiarism_level']
        )
    ]

    judgement_res = []
    for _ in data['comparasion']:
        for __ in _['result']['results']:
            if __['similarity'] == 0.:
                continue
            judgement_res.append(
                JudgementResult(
                    solution_to_judge_id=data['id'],
                    solution_to_compare_id=_['id'],
                    algorithm_id=__['algo_id'],
                    similarity=__['similarity'],
                    verdict=__['verdict']
                )
            )
    judgement_res.sort(key=lambda res: -res.similarity)
    vals.extend(judgement_res[:100])
    return vals


def dump_plagiarism_report(data):
    with transaction.atomic():
        results = _create_judgementresult_insert(data)
        [item.save() for item in results]

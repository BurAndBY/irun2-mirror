from django.db import transaction
from django.shortcuts import get_object_or_404

from solutions.models import Judgement, TestCaseResult

from workerstructs import WorkerTestingJob, WorkerProblem, WorkerFile, WorkerTestCase


def _make_problem(solution):
    if solution.ad_hoc_run is not None:
        run = solution.ad_hoc_run

        wtest = WorkerTestCase(0)
        wtest.input_resource_id = run.resource_id
        wtest.time_limit = run.time_limit
        wtest.memory_limit = run.memory_limit

        wproblem = WorkerProblem(run.id)
        wproblem.name = 'ad hoc'
        wproblem.input = WorkerFile(run.input_file_name)
        wproblem.output = WorkerFile(run.output_file_name)
        wproblem.tests = [wtest]
        return wproblem

    if solution.problem is not None:
        problem = solution.problem

        wtests = []
        for tc in problem.testcase_set.all().order_by('ordinal_number', 'id'):
            wtest = WorkerTestCase(tc.id)

            wtest.input = WorkerFile(tc.input_resource_id)
            wtest.answer = WorkerFile(tc.answer_resource_id)
            wtest.time_limit = tc.time_limit
            wtest.memory_limit = tc.memory_limit
            wtest.max_score = tc.points

            wtests.append(wtest)

        wproblem = WorkerProblem(problem.id)
        wproblem.name = problem.numbered_full_name()
        wproblem.input_file_name = problem.input_filename
        wproblem.output_file_name = problem.output_filename
        wproblem.tests = wtests
        return wproblem


def _make_job(judgement):
    solution = judgement.solution

    job = WorkerTestingJob(judgement.id)
    job.problem = _make_problem(solution)
    job.solution = solution
    job.stop_after_first_failed_test = False

    return job


def get_testing_job():
    judgement = Judgement.objects.filter(status=Judgement.WAITING).first()
    if judgement is not None:
        rows_updated = Judgement.objects.filter(id=judgement.id, status=Judgement.WAITING).update(status=Judgement.PREPARING)
        assert rows_updated in (0, 1)
        if rows_updated == 1:
            judgement = Judgement.objects.filter(id=judgement.id).first()
            return _make_job(judgement)
    return None


def put_testing_report(judgement_id, report):
    with transaction.atomic():
        rows_updated = Judgement.objects.filter(id=judgement_id).exclude(status=Judgement.WAITING).exclude(status=Judgement.DONE).update(status=Judgement.DONE)
        assert rows_updated in (0, 1)
        if rows_updated == 0:
            return

        judgement = get_object_or_404(Judgement, pk=judgement_id)
        judgement.outcome = report.outcome
        judgement.score = report.score
        judgement.max_score = report.max_score
        judgement.test_number = report.first_failed_test
        judgement.save()

        judgement.testcaseresult_set.all().delete()
        for t in report.tests:
            t.judgement_id = judgement.id
        TestCaseResult.objects.bulk_create(report.tests)

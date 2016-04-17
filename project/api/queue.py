from django.utils import timezone
from django.db import transaction

from common.outcome import Outcome
from problems.models import Validation, TestCaseValidation, ProblemRelatedSourceFile, TestCase
from solutions.models import Judgement, TestCaseResult, JudgementExtraInfo, JudgementLog, Challenge, ChallengedSolution

from .models import DbObjectInQueue
from .workerstructs import WorkerTestingJob, WorkerTestCase, WorkerProblem, WorkerFile, WorkerChecker, WorkerValidator, WorkerState


class IObjectInQueue(object):
    def __init__(self, db_obj_id):
        self._db_obj_id = db_obj_id

    def get_db_obj_id(self):
        return self._db_obj_id

    @classmethod
    def create(cls, db_obj):
        '''
        Returns None if DB object has unknown data.
        Must not modify the database.
        '''
        raise NotImplementedError()

    def persist(self, db_obj):
        '''
        May modify the database.
        '''
        raise NotImplementedError()

    def get_job(self):
        '''
        Must not modify the database.

        returns:
            WorkerTestingJob
        '''
        raise NotImplementedError()

    def update_state(self, state):
        '''
        args:
            state: WorkerState object
        '''
        raise NotImplementedError()

    def put_report(self, report):
        '''
        Is executed under transaction.

        args:
            report: WorkerTestingReport object
        '''
        raise NotImplementedError()


class ValidationInQueue(IObjectInQueue):
    def __init__(self, validation_id, db_obj_id=None):
        super(ValidationInQueue, self).__init__(db_obj_id)
        self._validation_id = validation_id

    @classmethod
    def create(cls, db_obj):
        if db_obj.validation_id is not None:
            return ValidationInQueue(validation_id=db_obj.validation_id, db_obj_id=db_obj.id)
        return None

    def persist(self, db_obj):
        db_obj.validation_id = self._validation_id

    def get_job(self):
        validation = Validation.objects.select_related('problem').get(pk=self._validation_id)

        job = WorkerTestingJob()
        job.problem = WorkerProblem(validation.problem.id)
        job.problem.name = validation.problem.numbered_full_name()

        job.problem.validator = WorkerValidator()
        job.problem.validator.source = validation.validator

        used_resource_ids = set()

        for test_case in validation.problem.testcase_set.all():
            # for validation we need unique inputs only
            resource_id = test_case.input_resource_id

            if resource_id not in used_resource_ids:
                test = WorkerTestCase(test_case.id)
                test.input = WorkerFile(resource_id)
                used_resource_ids.add(resource_id)
                job.problem.tests.append(test)

        return job

    def put_report(self, report):
        validation = Validation.objects.filter(pk=self._validation_id, validator_id__isnull=False).first()
        if validation is None:
            return

        validation.general_failure_reason = report.general_failure_reason or ''
        validation.is_pending = False
        validation.save()

        validation.testcasevalidation_set.all().delete()

        test_case_validations = []
        for test in report.tests:
            v = TestCaseValidation(
                validation=validation,
                input_resource_id=test.input_resource_id,
                is_valid=(test.outcome == Outcome.ACCEPTED),
                validator_message=test.checker_message,
            )
            test_case_validations.append(v)

        TestCaseValidation.objects.bulk_create(test_case_validations)

    def update_state(self, state):
        pass


class JudgementInQueue(IObjectInQueue):
    def __init__(self, judgement_id, db_obj_id=None):
        super(JudgementInQueue, self).__init__(db_obj_id)
        self._judgement_id = judgement_id

    @classmethod
    def create(cls, db_obj):
        if db_obj.judgement_id is not None:
            return JudgementInQueue(judgement_id=db_obj.judgement_id, db_obj_id=db_obj.id)
        return None

    def persist(self, db_obj):
        db_obj.judgement_id = self._judgement_id

    def get_job(self):
        judgement = Judgement.objects.select_related('solution').get(pk=self._judgement_id)
        job = WorkerTestingJob()
        job.problem = self._make_workerproblem(judgement.solution.problem)
        job.solution = judgement.solution
        job.stop_after_first_failed_test = judgement.solution.stop_on_fail
        return job

    @staticmethod
    def _make_workerproblem(problem):
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

        checker = problem.problemrelatedsourcefile_set.filter(file_type=ProblemRelatedSourceFile.CHECKER).first()
        if checker is not None:
            wproblem.checker = WorkerChecker(checker)

        return wproblem

    def put_report(self, report):
        judgement = Judgement.objects.get(pk=self._judgement_id)
        judgement.status = Judgement.DONE
        judgement.outcome = report.outcome
        judgement.score = report.score
        judgement.max_score = report.max_score
        judgement.test_number = report.first_failed_test
        judgement.save()

        gf_reason = report.general_failure_reason or ''
        gf_message = report.general_failure_message or ''

        JudgementExtraInfo.objects.\
            filter(pk=judgement.id).\
            update(finish_testing_time=timezone.now(), general_failure_reason=gf_reason, general_failure_message=gf_message)

        present_test_case_ids = TestCase.objects.\
            filter(problem__solution__judgement=judgement).\
            values_list('pk', flat=True)
        present_test_case_ids = set(present_test_case_ids)

        judgement.testcaseresult_set.all().delete()
        for t in report.tests:
            t.judgement_id = judgement.id
            if t.test_case_id not in present_test_case_ids:
                # the test case has probably been deleted while testing
                t.test_case_id = None

        TestCaseResult.objects.bulk_create(report.tests)

        judgement.judgementlog_set.all().delete()
        for log in report.logs:
            log.judgement = judgement
        JudgementLog.objects.bulk_create(report.logs)

    def update_state(self, state):
        Judgement.objects.filter(pk=self._judgement_id).exclude(status=Judgement.DONE).update(status=state.status, test_number=state.test_number)

        if state.status == Judgement.PREPARING:
            JudgementExtraInfo.objects.filter(pk=self._judgement_id).update(start_testing_time=timezone.now())


class ChallengedSolutionInQueue(IObjectInQueue):
    def __init__(self, challenged_solution_id, db_obj_id=None):
        super(ChallengedSolutionInQueue, self).__init__(db_obj_id)
        self._pk = challenged_solution_id

    @classmethod
    def create(cls, db_obj):
        if db_obj.challenged_solution_id is not None:
            return ChallengedSolutionInQueue(challenged_solution_id=db_obj.challenged_solution_id, db_obj_id=db_obj.id)
        return None

    def persist(self, db_obj):
        db_obj.challenged_solution_id = self._pk

    def get_job(self):
        cs = ChallengedSolution.objects.\
            select_related('solution', 'challenge', 'challenge__problem').\
            get(pk=self._pk)

        job = WorkerTestingJob()

        wtest = WorkerTestCase(0)
        wtest.input = WorkerFile(cs.challenge.input_resource_id)
        wtest.time_limit = cs.challenge.time_limit
        wtest.memory_limit = cs.challenge.memory_limit

        problem = cs.challenge.problem
        job.problem = WorkerProblem(problem.id)
        job.problem.name = problem.numbered_full_name()
        job.problem.input_file_name = problem.input_filename
        job.problem.output_file_name = problem.output_filename
        job.problem.tests = [wtest]
        job.problem.checker = WorkerChecker(None)
        job.problem.checker.kind = WorkerChecker.ACCEPT_ALL

        job.solution = cs.solution
        job.stop_after_first_failed_test = False
        return job

    def put_report(self, report):
        cs = ChallengedSolution.objects.get(pk=self._pk)
        cs.outcome = report.outcome
        if report.tests:
            test = report.tests[0]
            cs.output_resource_id = test.output_resource_id
            cs.stdout_resource_id = test.stdout_resource_id
            cs.stderr_resource_id = test.stderr_resource_id
            cs.exit_code = test.exit_code
            cs.time_used = test.time_used
            cs.memory_used = test.memory_used
        cs.save()

    def update_state(self, state):
        pass


'''
Common queue functions
'''


OBJECT_IN_QUEUE_CLASSES = [
    ValidationInQueue,
    JudgementInQueue,
    ChallengedSolutionInQueue,
]


def enqueue(obj, priority=10):
    ts = timezone.now()
    db_obj = DbObjectInQueue(creation_time=ts, last_update_time=ts, priority=priority)
    obj.persist(db_obj)
    db_obj.save()


def bulk_enqueue(objs, priority=10):
    ts = timezone.now()
    db_objs = []
    for obj in objs:
        db_obj = DbObjectInQueue(creation_time=ts, last_update_time=ts, priority=priority)
        obj.persist(db_obj)
        db_objs.append(db_obj)
    DbObjectInQueue.objects.bulk_create(db_objs)


def dequeue(worker_name):
    while True:
        db_obj = DbObjectInQueue.objects.\
            order_by('-priority', 'id').\
            filter(state=DbObjectInQueue.WAITING).\
            first()

        if db_obj is None:
            # no jobs
            return None

        with transaction.atomic():
            rows_updated = DbObjectInQueue.objects.\
                filter(pk=db_obj.pk, state=DbObjectInQueue.WAITING).\
                update(state=DbObjectInQueue.EXECUTING, last_update_time=timezone.now(), worker=worker_name)

            assert rows_updated in (0, 1)
            if rows_updated == 0:
                continue

            db_obj.refresh_from_db()

            for cls in OBJECT_IN_QUEUE_CLASSES:
                obj = cls.create(db_obj)
                if obj is not None:
                    obj.update_state(WorkerState(Judgement.PREPARING))
                    return obj
            return None


def finalize(db_obj_id):
    rows_updated = DbObjectInQueue.objects.\
        filter(pk=db_obj_id, state=DbObjectInQueue.EXECUTING).\
        update(state=DbObjectInQueue.DONE, last_update_time=timezone.now())

    assert rows_updated in (0, 1)
    if rows_updated == 1:
        db_obj = DbObjectInQueue.objects.get(pk=db_obj_id)

        for cls in OBJECT_IN_QUEUE_CLASSES:
            obj = cls.create(db_obj)
            if obj is not None:
                return obj


def update(db_obj_id):
    db_obj = DbObjectInQueue.objects.filter(pk=db_obj_id, state=DbObjectInQueue.EXECUTING).first()

    if db_obj is not None:
        for cls in OBJECT_IN_QUEUE_CLASSES:
            obj = cls.create(db_obj)
            if obj is not None:
                return obj

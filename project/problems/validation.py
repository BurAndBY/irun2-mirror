from .models import Validation, TestCaseValidation

from api.queue import ValidationInQueue, enqueue


def revalidate_testset(problem_id, clear=False):
    validation_id = Validation.objects.filter(problem_id=problem_id, validator_id__isnull=False).values_list('pk', flat=True).first()
    if validation_id is not None:
        if clear:
            TestCaseValidation.objects.filter(validation__problem_id=problem_id).delete()

        enqueue(ValidationInQueue(validation_id))

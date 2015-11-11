from .models import Judgement


def enqueue_new(solution):
    judgement = Judgement(
        solution=solution,
    )
    judgement.save()
    return judgement

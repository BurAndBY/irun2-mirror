from django.core.files.base import ContentFile
from django.utils import timezone

from api.queue import enqueue, JudgementInQueue
from common.networkutils import get_request_ip
from solutions.models import Solution, Judgement, JudgementExtraInfo
from storage.utils import store_with_metadata


def new_solution(request, form, problem_id=None):
    '''
    Returns new Solution object.
    Args:
        form: SolutionForm instance
    '''
    upload = form.cleaned_data['upload']
    if upload is None:
        # real file is not uploaded, we use text
        upload = ContentFile(form.cleaned_data['text'].encode('utf-8'), name=form.cleaned_data['filename'])

    source_code = store_with_metadata(upload)
    solution = Solution(author=request.user, ip_address=get_request_ip(request), reception_time=timezone.now(),
                        source_code=source_code, compiler=form.cleaned_data['compiler'], problem_id=problem_id)

    solution.save()
    return solution


def judge(solution, rejudge=None, set_best=True):
    judgement = Judgement(solution=solution, rejudge=rejudge)
    judgement.save()

    JudgementExtraInfo.objects.create(judgement=judgement, creation_time=timezone.now())

    priority = 10 if rejudge is None else 5
    enqueue(JudgementInQueue(judgement.id), priority)

    if set_best and solution.best_judgement_id is None:
        solution.best_judgement = judgement
        solution.save()

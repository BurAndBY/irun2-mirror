from django.core.files.base import ContentFile
from django.utils import timezone

from api.queue import enqueue, JudgementInQueue
from common.networkutils import get_request_ip
from proglangs.utils import guess_filename
from solutions.models import Solution, Judgement, JudgementExtraInfo
from storage.utils import store_with_metadata


def new_solution(request, compiler, text, upload, problem_id=None):
    '''
    Returns new Solution object.
    '''
    if upload is None:
        # real file is not uploaded, we use text
        filename = guess_filename(compiler.language, text)
        upload = ContentFile(text.encode('utf-8'), name=filename)

    source_code = store_with_metadata(upload)
    solution = Solution(author=request.user, ip_address=get_request_ip(request), reception_time=timezone.now(),
                        source_code=source_code, compiler=compiler, problem_id=problem_id)

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

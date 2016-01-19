from django.core.files.base import ContentFile
from django.utils import timezone

from common.networkutils import get_request_ip
from solutions.models import Solution, Judgement
import storage.utils
import proglangs.utils
from api.workerinteract import notify


def new_solution(request, compiler, text, upload, problem_id=None):
    '''
    Returns new Solution object.
    '''
    if upload is None:
        # real file is not uploaded, we use text
        filename = proglangs.utils.guess_filename(compiler.language, text)
        upload = ContentFile(text.encode('utf-8'), name=filename)

    source_code = storage.utils.store_with_metadata(upload)
    solution = Solution(author=request.user, ip_address=get_request_ip(request), reception_time=timezone.now(),
                        source_code=source_code, compiler=compiler, problem_id=problem_id)

    solution.save()
    return solution


def judge(solution, rejudge=None):
    judgement = Judgement(solution=solution, rejudge=rejudge)
    judgement.save()
    notify()

    if solution.best_judgement is None:
        solution.best_judgement = judgement
        solution.save()

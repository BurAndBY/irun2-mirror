from django.core.files.base import ContentFile
from django.utils import timezone

from solutions.models import Solution, Judgement
import storage.utils
import proglangs.utils
from api.workerinteract import notify


def new_solution(author, compiler, text, upload, problem=None):
    '''
    Returns new Solution object.
    '''
    if upload is None:
        # real file is not uploaded, we use text
        filename = proglangs.utils.guess_filename(compiler.language, text)
        upload = ContentFile(text.encode('utf-8'), name=filename)

    source_code = storage.utils.store_with_metadata(upload)
    solution = Solution(author=author, source_code=source_code, compiler=compiler, reception_time=timezone.now(), problem=problem)
    solution.save()
    return solution


def judge(solution, rejudge=None):
    judgement = Judgement(solution=solution, rejudge=rejudge)
    judgement.save()
    notify()

    if solution.best_judgement is None:
        solution.best_judgement = judgement
        solution.save()

from django.core.files.base import ContentFile
from django.utils import timezone

from api.queue import enqueue, bulk_enqueue, JudgementInQueue
from common.networkutils import get_request_ip
from solutions.models import Solution, Judgement, JudgementExtraInfo, Rejudge
from storage.utils import store_with_metadata


def new_solution(request, form, problem_id=None, stop_on_fail=False):
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
                        source_code=source_code, compiler=form.cleaned_data['compiler'], problem_id=problem_id, stop_on_fail=stop_on_fail)

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


def bulk_rejudge(solutions, author):
    '''
    solutions: queryset

    Note: should be launched inside DB transaction.
    '''
    rejudge = Rejudge.objects.create(author=author)

    judgements = []
    for solution_id, best_judgement_id in solutions.values_list('pk', 'best_judgement_id'):
        judgement = Judgement(solution_id=solution_id, rejudge=rejudge, judgement_before_id=best_judgement_id)
        judgements.append(judgement)

    Judgement.objects.bulk_create(judgements)

    # get back pk's of newly created objects
    judgement_ids = Judgement.objects.filter(rejudge=rejudge).values_list('pk', flat=True)

    ts = timezone.now()
    judgement_extra_infos = []
    for judgement_id in judgement_ids:
        info = JudgementExtraInfo(judgement_id=judgement_id, creation_time=ts)
        judgement_extra_infos.append(info)

    JudgementExtraInfo.objects.bulk_create(judgement_extra_infos)

    bulk_enqueue((JudgementInQueue(pk) for pk in judgement_ids), priority=5)

    return rejudge

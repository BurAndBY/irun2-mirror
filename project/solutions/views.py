from collections import namedtuple

from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.views import generic
from django.views.generic import View
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, render, render_to_response
from django.db import transaction
from django.template import RequestContext

from .forms import AdHocForm
from .models import AdHocRun, Solution, Judgement, Rejudge
from .actions import enqueue_new
from .tables import SolutionTable
from table.views import FeedDataView

from storage.storage import ResourceId, create_storage

from common.views import IRunnerPaginatedList

class AdHocView(View):
    template_name = 'solutions/ad_hoc.html'

    def get(self, request, *args, **kwargs):
        form = AdHocForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = AdHocForm(request.POST)
        judgement_id = None

        if form.is_valid():

            storage = create_storage()
            f = ContentFile(form.cleaned_data['input_data'].encode('utf-8'))
            resource_id = storage.save(f)

            run = AdHocRun(
                resource_id=resource_id,
                input_file_name='input.txt',
                output_file_name='output.txt',
                time_limit=2000,
                memory_limit=0,
            )

            run.save()

            f = ContentFile(form.cleaned_data['source_code'].encode('utf-8'))
            resource_id = storage.save(f)

            solution = Solution(
                ad_hoc_run=run,
                resource_id=resource_id,
                compiler=form.cleaned_data['compiler'],
                filename='',
            )

            solution.save()

            judjement = enqueue_new(solution)
            judgement_id = judjement.id

            #form.save()
            #return HttpResponseRedirect(reverse('problems:index'))

        return render(request, self.template_name, {'form': form, 'judgement_id': judgement_id})


class SolutionListView(IRunnerPaginatedList):
    paginate_by = 25

    def get_queryset(self):
        return Solution.objects.prefetch_related('compiler').select_related('best_judgement')


def show_judgement(request, judgement_id):
    judgement = get_object_or_404(Judgement, pk=judgement_id)
    test_results = judgement.testcaseresult_set.all()

    return render(request, 'solutions/judgement.html', {
        'judgement': judgement,
        'test_results': test_results,
    })


class CreateRejudgeView(View):
    def get(self, request, *args, **kwargs):
        ids = request.GET.getlist('id')
        return render(request, 'solutions/confirm_multiple.html', {'ids': ids})

    def post(self, request, *args, **kwargs):
        ids = request.GET.getlist('id')
        with transaction.atomic():
            rejudge = Rejudge.objects.create()
            judgements = [Judgement(solution_id=solution_id, rejudge=rejudge) for solution_id in ids]
            Judgement.objects.bulk_create(judgements)

        return HttpResponseRedirect(reverse('solutions:rejudge', args=[rejudge.id]))


RejudgeInfo = namedtuple('RejudgeInfo', ['solution', 'before', 'after'])


class RejudgeView(View):
    def get(self, request, rejudge_id):
        rejudge = get_object_or_404(Rejudge, pk=rejudge_id)
        object_list = []
        for new_judgement in rejudge.judgement_set.all().select_related('solution').select_related('solution__best_judgement'):
            solution = new_judgement.solution
            object_list.append(RejudgeInfo(solution, solution.best_judgement, new_judgement))

        return render(request, 'solutions/rejudge.html', {'committed': rejudge.committed, 'object_list': object_list})

    def post(self, request, rejudge_id):
        need_commit = ('commit' in request.POST)
        need_rollback = ('rollback' in request.POST)

        if (need_commit ^ need_rollback):
            target = True if need_commit else False
            num_rows = Rejudge.objects.filter(id=rejudge_id, committed=None).update(committed=target)
            if num_rows and need_commit:
                with transaction.atomic():
                    rejudge = get_object_or_404(Rejudge, pk=rejudge_id)
                    for new_judgement in rejudge.judgement_set.all().select_related('solution'):
                        solution = new_judgement.solution
                        solution.best_judgement = new_judgement
                        solution.save()

        return HttpResponseRedirect(reverse('solutions:rejudge', args=[rejudge_id]))


def ilist(request):
    objects = Solution.objects.all().prefetch_related('compiler').select_related('best_judgement')
    table = SolutionTable(objects)
    #return render(request, "solutions/ilist.html", {'table': table})
    return render_to_response("solutions/ilist.html", {"table": table},
                              context_instance=RequestContext(request))

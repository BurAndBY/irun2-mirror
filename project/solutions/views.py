from django.shortcuts import render

from django.views import generic
from django.views.generic import View
from django.core.files.base import ContentFile

from .forms import AdHocForm
from .models import AdHocRun, Solution
from .actions import enqueue_new

from storage.storage import ResourceId, create_storage


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
                programming_language=form.cleaned_data['programming_language'],
                filename='',
            )

            solution.save()

            judjement = enqueue_new(solution)
            judgement_id = judjement.id

            #form.save()
            #return HttpResponseRedirect(reverse('problems:index'))

        return render(request, self.template_name, {'form': form, 'judgement_id': judgement_id})


class SolutionListView(generic.ListView):
    def get_queryset(self):
        return Solution.objects.all().prefetch_related('compiler').select_related('best_judgement')

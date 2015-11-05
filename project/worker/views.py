from django.shortcuts import render
from django.views.generic.list import ListView
from .models import Job
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, StreamingHttpResponse
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import SuspiciousOperation
from storage.storage import create_storage, ResourceId
from django.http import Http404

import time
import threading
import json

condvar = threading.Condition()


class JobListView(ListView):
    model = Job
    template_name = 'worker/index.html'


def add_job(request, xxx):
    xxx = int(xxx)
    job = Job(x=xxx)

    with condvar:
        job.save()
        condvar.notify()

    url = reverse('worker:index')
    return HttpResponseRedirect(url)


def fetch_job():
    job = Job.objects.filter(status=Job.ENQUEUED).first()
    if job is not None:
        job.status = Job.PROCESSING
        job.save()
    return job


@csrf_exempt
def take_job(request):
    job = None

    with condvar:
        while True:
            job = fetch_job()
            if job is not None:
                break
            condvar.wait(timeout=5.0)

    if job is not None:
        return JsonResponse({'success': True, 'x': job.x})
    else:
        return JsonResponse({'success': False})


def _job_status_json(job):
    return {
        'status': job.status,
        'stage': job.stage,
        'onStageProgress': job.on_stage_progress,
        'onStageMax': job.on_stage_max,
    }


def _get_int(data, name, default=None):
    it = data.get(name)
    if it is not None:
        try:
            return int(it)
        except ValueError:
            raise SuspiciousOperation('unable to parse int from {0} value'.format(name))
    return default


@csrf_exempt
def job_status(request, job_id):
    if request.method == 'GET':
        job = get_object_or_404(Job, pk=job_id)
        return JsonResponse(_job_status_json(job))

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except ValueError:
            raise SuspiciousOperation('unable to parse JSON request body')

        job = get_object_or_404(Job, pk=job_id)

        new_stage = _get_int(data, 'stage')
        if new_stage is not None and new_stage != job.stage:
            job.stage = new_stage
            job.on_stage_progress = 0
            job.on_stage_max = 0

        job.on_stage_progress = _get_int(data, 'onStageProgress', default=job.on_stage_progress)
        job.on_stage_max = _get_int(data, 'onStageMax', default=job.on_stage_max)
        job.save()

        return JsonResponse(_job_status_json(job))


def job_result(request):
    pass


@csrf_exempt
def upload(request):
    print request.POST
    print request.FILES
    return JsonResponse({})


def download(request, resource_id):
    resource_id = ResourceId.parse(resource_id)

    storage = create_storage()
    data = storage.serve(resource_id)

    if data is None:
        raise Http404("Resource does not exist")

    response = StreamingHttpResponse(data.generator, content_type='application/octet-stream')
    response['Content-Length'] = data.size
    return response

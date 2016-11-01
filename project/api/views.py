import time

from django.conf import settings
from django.db import transaction
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import generic

from rest_framework import permissions
from rest_framework import serializers
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView

from proglangs.models import Compiler, CompilerDetails
from storage.storage import create_storage
from cauth.mixins import StaffMemberRequiredMixin
from common.cast import make_int_list_quiet
from contests.models import Printout

import plagiarism.plagiarism_api

from .models import DbObjectInQueue
from .queue import dequeue, update, finalize
from .serializers import parse_resource_id
from .serializers import WorkerTestingJobSerializer, WorkerTestingReportSerializer, WorkerStateSerializer, WorkerGreetingSerializer, PlagiarismJobSerializer


#
# File Stroage API
#


class WorkerTokenPermission(permissions.BasePermission):
    message = 'Correct Worker Token HTTP header is required.'

    def has_permission(self, request, view):
        token = request.META.get('HTTP_WORKER_TOKEN')
        return token == settings.WORKER_TOKEN


class WorkerAPIView(APIView):
    permission_classes = (WorkerTokenPermission,)


class FileStatusView(WorkerAPIView):
    '''
    Pass HTTP GET request with id query params.

    Example: <code>/fs/status?id=...&id=...&id=...</code>
    '''
    def get(self, request, format=None):
        ids = request.query_params.getlist('id')
        resource_ids = [parse_resource_id(s) for s in set(ids)]

        storage = create_storage()
        availabilities = storage.check_availability(resource_ids)

        result = {}
        for resource_id, avail in zip(resource_ids, availabilities):
            result[str(resource_id)] = avail

        return Response(result, status=status.HTTP_200_OK)


class FileView(WorkerAPIView):
    parser_classes = (FileUploadParser,)

    def put(self, request, filename, format=None):
        file_obj = request.FILES['file']

        target_resource_id = parse_resource_id(filename)
        storage = create_storage()
        resource_id = storage.save(file_obj)

        if resource_id != target_resource_id:
            raise serializers.ValidationError('The uploaded data has id {0} instead of {1}'.format(resource_id, target_resource_id))

        return Response(status=status.HTTP_200_OK)

    def get(self, request, filename, format=None):
        resource_id = parse_resource_id(filename)
        storage = create_storage()

        data = storage.serve(resource_id)

        if data is None:
            raise NotFound("Resource does not exist")

        response = StreamingHttpResponse(data.generator, content_type='application/octet-stream')
        response['Content-Length'] = data.size
        return response


#
# Testing Job/Report API
#

class JobTakeView(WorkerAPIView):
    def post(self, request, format=None):
        serializer = WorkerGreetingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        greeting = serializer.save()

        obj = dequeue(greeting.name)
        if obj is None:
            raise Http404('Nothing to test')

        job = obj.get_job()
        job.id = obj.get_db_obj_id()
        serializer = WorkerTestingJobSerializer(job)
        return Response(serializer.data)


class JobPutResultView(WorkerAPIView):
    def put(self, request, job_id, format=None):
        serializer = WorkerTestingReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save()

        with transaction.atomic():
            obj = finalize(job_id)
            if obj is not None:
                obj.put_report(report)

        return Response(['ok'])


class JobPutStateView(WorkerAPIView):
    def put(self, request, job_id, format=None):
        serializer = WorkerStateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        state = serializer.save()

        obj = update(job_id)
        if obj is not None:
            obj.update_state(state)
        return Response(['ok'])


class CompilerSettingsView(WorkerAPIView):
    def post(self, request, format=None):
        for info in request.data:
            handle = info.get('handle')
            if handle is not None:
                compiler = Compiler.objects.filter(handle=handle).first()
                if compiler is not None:
                    details = CompilerDetails(
                        pk=compiler.id,
                        compile_command=info.get('compile_command', ''),
                        run_command=info.get('run_command', ''),
                    )
                    details.save()
        return Response(['ok'])


'''
Queue viewer
'''


class QueueView(StaffMemberRequiredMixin, generic.View):
    template_name = 'api/queue.html'

    def get(self, request):
        new_objects = DbObjectInQueue.objects.exclude(state=DbObjectInQueue.DONE).order_by('-priority', 'id').all()
        last_objects = DbObjectInQueue.objects.filter(state=DbObjectInQueue.DONE).order_by('-last_update_time', 'id').all()[:10]
        return render(request, self.template_name, {'new_objects': new_objects, 'last_objects': last_objects})

    def post(self, request):
        ids = make_int_list_quiet(request.POST.getlist('id'))
        if ids:
            DbObjectInQueue.objects.filter(pk__in=ids).update(state=DbObjectInQueue.WAITING)
        return redirect('api:queue')


'''
Plagiarism Api
'''


class PlagiarismTakeView(WorkerAPIView):
    def get(self, request, format=None):
        return self.post(request, format)

    def post(self, request, format=None):
        job = plagiarism.plagiarism_api.get_testing_job()

        if job is None:
            raise Http404('Nothing to test')

        serializer = PlagiarismJobSerializer(job)
        return Response(serializer.data)


class PlagiarismPutView(WorkerAPIView):
    def put(self, request, format=None):
        plagiarism.plagiarism_api.dump_plagiarism_report(request.data)
        return Response(['ok'])


class SleepView(WorkerAPIView):
    def get(self, request):
        secs = request.GET.get('secs', 0.)
        try:
            secs = float(secs)
        except (TypeError, ValueError):
            secs = 0.

        time.sleep(secs)

        return Response(['ok'])


'''
Printing API
'''


class PrintingView(WorkerAPIView):
    def get(self, request):
        result = []
        printouts = Printout.objects.filter(status=Printout.WAITING).order_by('timestamp')
        for printout in printouts:
            data = {
                'id': printout.id,
                'text': printout.text,
                'room': printout.room,
                'user': printout.user.get_full_name(),
                'timestamp': timezone.localtime(printout.timestamp).strftime('%d.%m.%Y %H:%M:%S')
            }
            result.append(data)
        return Response(result)


class PrintingDoneView(WorkerAPIView):
    def post(self, request, printout_id):
        Printout.objects.filter(pk=printout_id, status=Printout.WAITING).update(status=Printout.DONE)
        return Response('OK')

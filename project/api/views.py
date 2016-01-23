from django.conf import settings
from django.http import Http404
from django.http import StreamingHttpResponse

from rest_framework import permissions
from rest_framework import serializers
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView

from storage.storage import create_storage

from .serializers import WorkerTestingJobSerializer, WorkerTestingReportSerializer, WorkerStateSerializer, parse_resource_id
import workerinteract

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

        print format
        response = StreamingHttpResponse(data.generator, content_type='application/octet-stream')
        response['Content-Length'] = data.size
        return response


#
# Testing Job/Report API
#


class JobTakeView(WorkerAPIView):
    def get(self, request, format=None):
        return self.post(request, format)

    def post(self, request, format=None):
        # job = workerinteract.get_testing_job()
        job = workerinteract.wait_for_testing_job()
        print request.data
        if job is None:
            raise Http404('Nothing to test')

        serializer = WorkerTestingJobSerializer(job)
        return Response(serializer.data)


class JobPutResult(WorkerAPIView):
    def put(self, request, job_id, format=None):
        serializer = WorkerTestingReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save()

        workerinteract.put_testing_report(job_id, report)
        return Response(['ok'])


class JobPutState(WorkerAPIView):
    def put(self, request, job_id, format=None):
        serializer = WorkerStateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        state = serializer.save()

        workerinteract.put_state(job_id, state)
        return Response(['ok'])

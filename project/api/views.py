import re
import six

from common.enum import JudgementStatusEnum

from django.db import transaction
from django.http import Http404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from rest_framework import serializers
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView

from solutions.models import Judgement, Outcome, TestCaseResult
from storage.storage import ResourceId, create_storage


def _serialize_problem(solution):
    if solution.ad_hoc_run is not None:
        run = solution.ad_hoc_run
        return {
            'inputFileName': run.input_file_name,
            #'outputFileName': run.output_file_name,
            'tests': [
                {
                    'input': {
                        'resourceId': str(run.resource_id),
                    },
                    'timeLimit': run.time_limit,
                    'memoryLimit': run.memory_limit,
                    'maxScore': 0,
                }
            ]
        }
    return {}


def _serialize_solution(solution):
    return {
        'programmingLanguage': solution.programming_language.handle,
        'resourceId': str(solution.resource_id),
        'filename': solution.filename,
    }


def _serialize_job(judgement):
    return {
        'id': str(judgement.id),
        'solution': _serialize_solution(judgement.solution),
        'stopAfterFirstFailedTest': False,
        'problem': _serialize_problem(judgement.solution),
    }


def _parse_resource_id(string):
    try:
        return ResourceId.parse(string)
    except ValueError as e:
        raise serializers.ValidationError('Unable to parse resource id: {0}'.format(e))


class FileStatusView(APIView):
    '''
    Pass HTTP GET request with id query params.

    Example: <code>/fs/status?id=...&id=...&id=...</code>
    '''
    def get(self, request, format=None):
        ids = request.query_params.getlist('id')
        resource_ids = [_parse_resource_id(s) for s in set(ids)]

        storage = create_storage()
        availabilities = storage.check_availability(resource_ids)

        result = {}
        for resource_id, avail in zip(resource_ids, availabilities):
            result[str(resource_id)] = avail

        return Response(result, status=status.HTTP_200_OK)


class FileView(APIView):
    parser_classes = (FileUploadParser,)

    def put(self, request, filename, format=None):
        file_obj = request.FILES['file']

        target_resource_id = _parse_resource_id(filename)
        storage = create_storage()
        resource_id = storage.save(file_obj)

        if resource_id != target_resource_id:
            raise serializers.ValidationError('The uploaded data has id {0} instead of {1}'.format(resource_id, target_resource_id))

        return Response(status=status.HTTP_200_OK)

    def get(self, request, filename, format=None):
        resource_id = _parse_resource_id(filename)
        storage = create_storage()

        data = storage.serve(resource_id)

        if data is None:
            raise NotFound("Resource does not exist")

        print format
        response = StreamingHttpResponse(data.generator, content_type='application/octet-stream')
        response['Content-Length'] = data.size
        return response


def fetch_job():
    job = Judgement.objects.filter(status=Judgement.WAITING).first()
    if job is not None:
        #job.status = Job.PROCESSING
        #job.save()
        pass
    return job


class JobTakeView(APIView):
    def get(self, request, format=None):
        judgement = fetch_job()
        result = _serialize_job(judgement)
        return Response(result)

    def post(self, request, format=None):
        print request.data
        judgement = fetch_job()
        result = _serialize_job(judgement)
        return Response(result)


def _enum_from_string(cls, data):
    if not isinstance(data, six.string_types):
        msg = 'Incorrect type. Expected a string, but got {0}'
        raise serializers.ValidationError(msg.format(type(data).__name__))

    if len(data) == 0:
        raise serializers.ValidationError('String is empty.')

    if not re.match(r'^[A-Z]+(_[A-Z]+)*$', data):
        raise serializers.ValidationError('Incorrect format. Expected capitalized Latin string with possible inner underscores.')

    if not hasattr(cls, data):
        raise serializers.ValidationError('Unknown value of {0} enumeration: `{1}`'.format(cls.__name__, data))

    return getattr(cls, data)


# Intermediate entity
class TestingReport(object):
    def __init__(self, outcome, first_failed_test, tests):
        self.outcome = outcome
        self.first_failed_test = first_failed_test
        self.tests = tests


class OutcomeField(serializers.Field):
    def to_internal_value(self, data):
        return _enum_from_string(Outcome, data)


class TestCaseResultSerializer(serializers.Serializer):
    outcome = OutcomeField()
    exit_code = serializers.IntegerField(default=0)
    time_limit = serializers.IntegerField(min_value=0, default=0)
    time_used = serializers.IntegerField(min_value=0, default=0)
    memory_limit = serializers.IntegerField(min_value=0, default=0)
    memory_used = serializers.IntegerField(min_value=0, default=0)
    score = serializers.IntegerField(min_value=0, default=0)
    max_score = serializers.IntegerField(min_value=0, default=0)
    checker_message = serializers.CharField(allow_blank=True, default='')

    def create(self, validated_data):
        return TestCaseResult(**validated_data)


class TestCaseResultField(serializers.Field):
    def to_internal_value(self, data):
        serializer = TestCaseResultSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.save()


class TestingReportSerializer(serializers.Serializer):
    outcome = OutcomeField()
    first_failed_test = serializers.IntegerField(min_value=0, required=False, default=0)
    tests = serializers.ListField(child=TestCaseResultField())

    def create(self, validated_data):
        return TestingReport(**validated_data)


class JobPutResult(APIView):
    def put(self, request, job_id, format=None):
        serializer = TestingReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        testing_report = serializer.save()

        with transaction.atomic():
            judgement = get_object_or_404(Judgement, pk=job_id)
            judgement.outcome = testing_report.outcome
            for t in testing_report.tests:
                t.judgement = judgement
                t.save()

        return Response(['ok'])

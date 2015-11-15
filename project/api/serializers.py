import re
import six

from rest_framework import serializers

from solutions.models import Outcome, TestCaseResult
from storage.storage import ResourceId
from .workerstructs import WorkerTestingReport


def parse_resource_id(string):
    try:
        return ResourceId.parse(string)
    except ValueError as e:
        raise serializers.ValidationError('Unable to parse resource id: {0}'.format(e))


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


class ResourceIdField(serializers.Field):
    def to_internal_value(self, data):
        return parse_resource_id(data)

    def to_representation(self, obj):
        return str(obj)


class OutcomeField(serializers.Field):
    def to_internal_value(self, data):
        return _enum_from_string(Outcome, data)


class SolutionSerializer(serializers.Serializer):
    compiler = serializers.CharField(read_only=True, source='compiler.handle')
    resource_id = ResourceIdField(read_only=True)
    filename = serializers.CharField(read_only=True)


class WorkerFileSerializer(serializers.Serializer):
    resource_id = ResourceIdField(read_only=True)


class WorkerTestCaseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    input = WorkerFileSerializer()
    answer = WorkerFileSerializer()
    time_limit = serializers.IntegerField(read_only=True)
    memory_limit = serializers.IntegerField(read_only=True)
    max_score = serializers.IntegerField(read_only=True)


class WorkerProblemSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    input_file_name = serializers.CharField(read_only=True)
    output_file_name = serializers.CharField(read_only=True)
    tests = WorkerTestCaseSerializer(read_only=True, many=True)


class WorkerTestingJobSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    problem = WorkerProblemSerializer(read_only=True)
    solution = SolutionSerializer()


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


class WorkerTestingReportSerializer(serializers.Serializer):
    outcome = OutcomeField()
    first_failed_test = serializers.IntegerField(min_value=0, required=False, default=0)
    score = serializers.IntegerField(min_value=0, required=False, default=0)
    max_score = serializers.IntegerField(min_value=0, required=False, default=0)
    tests = serializers.ListField(child=TestCaseResultField())

    def create(self, validated_data):
        return WorkerTestingReport(**validated_data)

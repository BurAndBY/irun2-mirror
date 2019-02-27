from rest_framework import serializers

from .structs import PreviewSource


class PreviewSourceSerializer(serializers.Serializer):
    tex = serializers.CharField()
    inline = serializers.BooleanField()

    def create(self, validated_data):
        return PreviewSource(**validated_data)


class PreviewResultSerializer(serializers.Serializer):
    html = serializers.CharField()

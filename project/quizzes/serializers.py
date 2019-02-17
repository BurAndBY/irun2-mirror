from rest_framework import serializers

from quizzes.quizstructs import QuizAnswer, QuizAnswersData, SaveAnswerMessage, QuestionChoice, QuestionData, \
    RelationData, RelationsData


class QuizAnswerSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=0, required=True)
    chosen = serializers.BooleanField(default=False)
    user_answer = serializers.CharField(max_length=16383, default=None, allow_blank=True, allow_null=True)


class QuizAnswersDataSerializer(serializers.Serializer):
    answers = serializers.ListField(child=QuizAnswerSerializer())

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        answers = [QuizAnswer(**answer_data) for answer_data in answers_data]
        return QuizAnswersData(answers)


class SaveAnswerMessageSerializer(serializers.Serializer):
    message = serializers.CharField(required=False)

    def create(self, validated_data):
        return SaveAnswerMessage(**validated_data)


class QuestionChoiceSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=0, default=None, required=False, allow_null=True)
    is_right = serializers.BooleanField(required=True)
    text = serializers.CharField(required=True, max_length=200)


class QuestionDataSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=0, default=None, required=False, allow_null=True)
    text = serializers.CharField(required=True, max_length=16383)
    type = serializers.CharField(required=True)
    choices = serializers.ListField(child=QuestionChoiceSerializer())

    def create(self, validated_data):
        choices_data = validated_data.pop('choices')
        choices = [QuestionChoice(**choice_data) for choice_data in choices_data]
        return QuestionData(validated_data.pop('id'), validated_data.pop('text'), validated_data.pop('type'), choices)


class RelationDataSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=0, required=True)
    points = serializers.FloatField(min_value=0)
    name = serializers.CharField(max_length=100, default=None, allow_blank=True, allow_null=True)


class RelationsDataSerializer(serializers.Serializer):
    rels = serializers.ListField(child=RelationDataSerializer())

    def create(self, validated_data):
        rels_data = validated_data.pop('rels')
        rels = [RelationData(**rel_data) for rel_data in rels_data]
        return RelationsData(rels)
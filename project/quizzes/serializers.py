from rest_framework import serializers

from quizzes.quizstructs import QuizAnswer, QuizAnswersData, SaveAnswerMessage


class QuizAnswerSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=0, required=True)
    chosen = serializers.BooleanField(default=False)
    user_answer = serializers.CharField(max_length=100, default=None, allow_blank=True, allow_null=True)


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

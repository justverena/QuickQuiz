from rest_framework import serializers
from .models import Quiz, Question, Option, Session, Answer

class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'teacher_id', 'created_at', 'updated_at',]
        read_only_fields = ['id', 'created_at', 'updated_at']

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = "__all__"

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'quiz', 'text', 'type', 'points', 'options'] 
        read_only_fields = ['id']

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = "__all__"


class AnswerSerializer(serializers.ModelSerializer):
    selected_options = serializers.ListField(
        child=serializers.UUIDField(format="hex_verbose"),
        allow_empty=True
    )
    student_id = serializers.UUIDField(required=False)
    is_correct = serializers.BooleanField(read_only=True)

    class Meta:
        model = Answer
        fields = ["id", "session", "student_id", "question", "selected_options", "is_correct"]
        read_only_fields = ["id", "is_correct"]

    def validate(self, attrs):
        question = attrs["question"]
        valid_ids = set(question.options.values_list("id", flat=True))
        received = set(attrs["selected_options"])
        if not received.issubset(valid_ids):
            raise serializers.ValidationError(
                {"selected_options": "Часть опций не относится к этому вопросу."}
            )
        return attrs

    def create(self, validated_data):
        question = validated_data["question"]
        selected = set(validated_data["selected_options"])
        correct_ids = set(
             question.options.filter(is_correct=True).values_list("id", flat=True)
        )
        validated_data["is_correct"] = (selected == correct_ids)
        return super().create(validated_data)
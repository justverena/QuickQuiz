from rest_framework import serializers
from .models import Quiz, Question, Option, Session, Answer

class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'teacher_id', 'created_at', 'updated_at',]
        read_only_fields = ['id', 'created_at', 'updated_at']

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'quiz', 'text', 'type', 'points']
        read_only_fields = ['id']

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = "__all__"


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = "__all__"

from rest_framework import serializers
from quizzes.models import Answer, Option

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = [
            'id',
            'session',
            'student_id',
            'question',
            'selected_options',
            'is_correct',
            'submitted_at'
        ]
        read_only_fields = ['id', 'student_id', 'is_correct', 'submitted_at']

    def validate(self, data):
        if 'student_id' in self.initial_data:
            raise serializers.ValidationError(
                {"student_id": "You cannot specify student_id manually."}
            )
        
        instance = getattr(self, 'instance', None)
        question = data.get('question') or getattr(instance, 'question', None)
        selected_options = data.get('selected_options', [])

        if not question:
            raise serializers.ValidationError({"question": "Question is required."})

        if selected_options:
            valid_option_ids = set(
                Option.objects.filter(question=question).values_list('id', flat=True)
            )
            invalid = [opt for opt in selected_options if opt not in valid_option_ids]
            if invalid:
                raise serializers.ValidationError({
                    "selected_options": f"Invalid options for question {question.id}: {invalid}"
                })

        return data

    def create(self, validated_data):
        answer = super().create(validated_data)

        correct_option_ids = set(
            Option.objects.filter(question=answer.question, is_correct=True)
                          .values_list('id', flat=True)
        )
        answer.is_correct = set(answer.selected_options) == correct_option_ids
        answer.save()

        return answer
from rest_framework import serializers
from .models import Quiz, Question, Option, Session

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
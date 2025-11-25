from rest_framework import serializers
from .models import Quiz, Question, Option, Session, Answer

class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description',
            'teacher_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'index', 'question', 'text']
        read_only_fields = ['id']


class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            'id', 'quiz_id', 'index', 'text',
            'correct_option_index', 'timer',
            'type', 'points', 'options'
        ]
        read_only_fields = ['id']



class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = [
            'id', 'quiz_id', 'teacher_id',
            'invite_code', 'status',
            'current_question_index', 'start_time',
            'end_time', 'duration',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'teacher_id', 'invite_code', 'status', 'created_at', 'updated_at']


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
        ]
        read_only_fields = ['id', 'student_id', 'is_correct']

    def validate(self, data):
        request = self.context.get('request')
        data['student_id'] = request.user.id

        question = data.get('question')
        selected = data.get('selected_options', [])

        if question.type == 'single' and len(selected) != 1:
            if len(selected) != 1:
                raise serializers.ValidationError(
                    {"selected_options": "Must contain exactly one option index for single-choice question."}
                )

        # Проверяем — указанные индексы действительно существуют
        valid_uuids = set(
            question.options.values_list('id', flat=True)
        )
        invalid = [i for i in selected if i not in valid_uuids]
        if invalid:
            raise serializers.ValidationError({
                "selected_options": f"Invalid option UUIDs: {invalid}"
            })

        return data
        
        valid_indices = set(
            question.options.values_list('index', flat=True)
        )
        invalid = [i for i in selected if i not in valid_indices]
        if invalid:
            raise serializers.ValidationError(
                {"selected_options": f"Invalid option indices: {invalid}"}
            )

        return data

    def create(self, validated_data):
        answer = super().create(validated_data)

        # Проверка правильности ответа через correct_option_index
        correct_index = answer.question.correct_option_index
        correct_option_id = answer.question.options.get(index=correct_index).id

        if answer.question.type == 'single':
            answer.is_correct = (answer.selected_options == [correct_option_id])
        else:  # multiple
            answer.is_correct = (correct_option_id in answer.selected_options)

        answer.save(update_fields=['is_correct'])
        return answer

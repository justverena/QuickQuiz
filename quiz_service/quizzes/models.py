from django.db import models
import uuid
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
from django.conf import settings


class Quiz(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    teacher_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPES = (
        ('single', 'Single choice'),
        ('multiple', 'Multiple choice'),
        ('text', 'Text answer'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz_id = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    index = models.IntegerField(default=0)
    text = models.TextField()
    
    #денормализация опшена (закоментить модель опшенов)
    #options = JSONField(default=list)
    
    correct_option_index = models.IntegerField(default=0)
    timer = models.IntegerField(help_text="Seconds to answer")
    type = models.CharField(max_length=50, choices=QUESTION_TYPES, default='single')
    points = models.IntegerField(default=1)

    def __str__(self):
        return f"Question ({self.quiz_id.title}): {self.text[:30]}"


class Option(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    index = models.IntegerField(default=0)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)

    def __str__(self):
        return f"Option for {self.question.text[:20]}: {self.text[:20]}"

class Session(models.Model):
    STATUS_CHOICES = (
        ('waiting', 'Waiting'),
        ('in_progress', 'In Progress'),
        ('finished', 'Finished'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz_id = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='sessions')
    teacher_id = models.UUIDField(null=False)
    # teacher_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions")
    invite_code = models.CharField(max_length=6, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    current_question_index = models.IntegerField(default=0)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(help_text="Duration in minutes", default=300)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session for {self.quiz.title} ({self.invite_code})"

class SessionPlayer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="players")
    student_id = models.UUIDField(null=True, blank=True)
    nickname = models.CharField(max_length=100)
    final_score = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.nickname} in {self.session.invite_code}"

    
class Answer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='answers')
    student_id = models.UUIDField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    selected_options = ArrayField(models.UUIDField(), blank=True, default=list)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Answer by {self.student_id} for {self.question.text[:20]}"
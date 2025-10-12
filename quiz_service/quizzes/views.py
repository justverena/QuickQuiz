from rest_framework import viewsets
from .models import Quiz, Question, Option, Session
from .serializers import QuizSerializer, QuestionSerializer, OptionSerializer, SessionSerializer

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all().order_by('-created_at')
    serializer_class = QuizSerializer

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

class OptionViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
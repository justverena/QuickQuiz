from rest_framework import viewsets
from .models import Quiz, Question, Option, Session
from .serializers import QuizSerializer, QuestionSerializer, OptionSerializer, SessionSerializer
from .permissions import IsTeacher, IsStudent
from rest_framework.permissions import IsAuthenticated

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all().order_by('-created_at')
    serializer_class = QuizSerializer
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsTeacher]
        else:
            permission_classes = [IsAuthenticated]
        return [p() for p in permission_classes]

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsTeacher]
        else:
            permission_classes = [IsAuthenticated]
        return [p() for p in permission_classes]
    

class OptionViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsTeacher]
        else:
            permission_classes = [IsAuthenticated]
        return [p() for p in permission_classes]


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsTeacher]
        else:
            permission_classes = [IsAuthenticated]
        return [p() for p in permission_classes]
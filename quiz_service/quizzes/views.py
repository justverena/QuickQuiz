from rest_framework import viewsets, status
from .models import Quiz, Question, Option, Session
from .serializers import QuizSerializer, QuestionSerializer, OptionSerializer, SessionSerializer
from .permissions import IsTeacher, IsStudent
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.response import Response
from rest_framework.decorators import action

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
    
class StudentSessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    @extend_schema(exclude=True)
    def create(self, request, *args, **kwargs):
        if getattr(request.user, 'role', None) != 'teacher':
            return Response({"detail": "Creating sessions is not allowed."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def update(self, request, *args, **kwargs):
        if getattr(request.user, 'role', None) != 'teacher':
            return Response({"detail": "Updating sessions is not allowed."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def partial_update(self, request, *args, **kwargs):
        if getattr(request.user, 'role', None) != 'teacher':
            return Response({"detail": "Updating sessions is not allowed."}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def destroy(self, request, *args, **kwargs):
        if getattr(request.user, 'role', None) != 'teacher':
            return Response({"detail": "Deleting sessions is not allowed."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) == 'teacher':
            return Session.objects.filter(quiz__teacher_id=user.id)
        elif getattr(user, 'role', None) == 'student':
            return Session.objects.none()
        return Session.objects.none()

    @action(detail=False, methods=['get'], url_path='get-by-invite', url_name='get-by-invite')
    def get_by_invite_code(self, request):
        if getattr(request.user, 'role', None) != 'student':
            return Response({"detail": "Only students can join sessions via invite code."},
                            status=status.HTTP_403_FORBIDDEN)
        invite_code = request.query_params.get('invite_code')
        if not invite_code:
            return Response({"detail": "Invite code is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            session = Session.objects.get(invite_code=invite_code)
        except Session.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(session)
        return Response(serializer.data)
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Session, Answer
from .serializers import SessionSerializer, AnswerSerializer
from .permissions import IsStudent

from drf_spectacular.utils import extend_schema, OpenApiParameter

class AnswerViewSet(viewsets.ModelViewSet):
    serializer_class = AnswerSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        return Answer.objects.filter(student_id=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(student_id=self.request.user.id)

    @extend_schema(exclude=True)
    def update(self, request, *args, **kwargs):
        return Response({"detail": "Updating answers is not allowed."}, status=status.HTTP_403_FORBIDDEN)

    @extend_schema(exclude=True)
    def partial_update(self, request, *args, **kwargs):
        return Response({"detail": "Updating answers is not allowed."}, status=status.HTTP_403_FORBIDDEN)
    
    @extend_schema(exclude=True)
    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Deleting answers is not allowed."}, status=status.HTTP_403_FORBIDDEN)
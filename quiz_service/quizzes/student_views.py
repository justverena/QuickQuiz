
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied
from .models import Answer
from .serializers import AnswerSerializer
from quizzes.permissions import IsStudent 
from quizzes.permissions import IsTeacher 

class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer

    def _role(self):
        role = None
        if isinstance(getattr(self.request, "auth", None), dict):
            role = self.request.auth.get("role")
        if role is None and hasattr(self.request.user, "role"):
            role = getattr(self.request.user, "role", None)
        return role

    def _current_user_id(self):
        if isinstance(getattr(self.request, "auth", None), dict):
            return str(self.request.auth.get("user_id"))
        return str(getattr(self.request.user, "id", ""))

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsStudent]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [p() for p in permission_classes]

    def get_queryset(self):
        role = self._role()
        if role == "student":
            return Answer.objects.filter(student_id=self._current_user_id())
        return Answer.objects.all()

    def perform_create(self, serializer):
        serializer.save(student_id=self._current_user_id())

    def perform_update(self, serializer):
        instance = self.get_object()
        if str(instance.student_id) != self._current_user_id():
            raise PermissionDenied("You can only modify your own answers.")
        serializer.save()

    def perform_destroy(self, instance):
        if str(instance.student_id) != self._current_user_id():
            raise PermissionDenied("You can only delete your own answers.")
        instance.delete()

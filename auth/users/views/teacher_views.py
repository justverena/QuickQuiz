from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from users.permissions import IsTeacher

class TeacherApiView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def get(self, request):
        return Response({"msg": "hello teacher, you may add your test"})
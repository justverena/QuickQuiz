from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from users.permissions import IsStudent
from users.serializers import UserSerializer

class StudentApiView(APIView):
    serializer_class = UserSerializer 
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request):
        return Response({"msg": "hello student, you may join your test"})
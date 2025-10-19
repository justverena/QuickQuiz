from rest_framework import generics, permissions, status, viewsets, serializers
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from users.models import User
from users.serializers import UserSerializer
from users.permissions import IsOwner
from rest_framework.exceptions import PermissionDenied
from django.http import Http404
from users.utils.logger import log_endpoint

User = get_user_model()

class ValidateTokenSerializer(serializers.Serializer):
    token = serializers.CharField(required=False) 
    
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    
    @log_endpoint
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class UserViewSet(viewsets.GenericViewSet, 
                  generics.RetrieveAPIView, 
                  generics.UpdateAPIView, 
                  generics.DestroyAPIView):
    http_method_names = ['get', 'patch', 'delete']
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOwner]
    
    def get_operation_id_base(self, *args, **kwargs):
        return f"{self.action}_user"

    
    def get_queryset(self):
        user = self.request.user
        try:
            is_admin = user.role.name == "admin"
        except Exception:
            is_admin = False

        if is_admin:
            return User.objects.all()
        return User.objects.filter(id=user.id)
    
    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            raise PermissionDenied("You do not have permission to access this user.")
    @log_endpoint
    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
    
    @log_endpoint
    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        return super().update(request, *args, **kwargs)
    
    @log_endpoint
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        return super().destroy(request, *args, **kwargs)

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['role'] = user.role.name if hasattr(user, 'role') else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        ordered_data = {
            "access": data["access"],
            "refresh": data["refresh"]
        }
        return ordered_data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    
    @log_endpoint
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class MyTokenRefreshView(TokenRefreshView):
    pass

class MeView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user
    
    @log_endpoint
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

# class InternalValidateTokenView(APIView):
#     serializer_class = ValidateTokenSerializer
#     authentication_classes = [JWTAuthentication]
#     permission_classes = []

#     def post(self, request):
#         auth_header = request.headers.get("Authorization")
#         token_str = None

#         if auth_header and auth_header.startswith("Bearer "):
#             token_str = auth_header.split(" ")[1]
#         elif "token" in request.data:
#             token_str = request.data.get("token")
#         else:
#             return Response(
#                 {"detail": "Authorization header or token missing"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         jwt_auth = JWTAuthentication()
#         try:
#             validated_token = jwt_auth.get_validated_token(token_str)
#             user = jwt_auth.get_user(validated_token)

#             return Response({
#                 "user_id": str(user.id),
#                 "username": user.username,
#                 "role": user.role.name if hasattr(user, 'role') else None,
#                 "is_valid": True
#             }, status=status.HTTP_200_OK)

#         except (InvalidToken, TokenError):
#             return Response(
#                 {"is_valid": False, "detail": "Invalid or expired token"},
#                 status=status.HTTP_401_UNAUTHORIZED
#             )

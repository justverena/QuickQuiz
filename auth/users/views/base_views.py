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

User = get_user_model()

class ValidateTokenSerializer(serializers.Serializer):
    token = serializers.CharField(required=False) 

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['role'] = user.role.name if hasattr(user, 'role') else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class MyTokenRefreshView(TokenRefreshView):
    pass

class MeView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class InternalValidateTokenView(APIView):
    serializer_class = ValidateTokenSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = []

    def post(self, request):
        auth_header = request.headers.get("Authorization")
        token_str = None

        if auth_header and auth_header.startswith("Bearer "):
            token_str = auth_header.split(" ")[1]
        elif "token" in request.data:
            token_str = request.data.get("token")
        else:
            return Response(
                {"detail": "Authorization header or token missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        jwt_auth = JWTAuthentication()
        try:
            validated_token = jwt_auth.get_validated_token(token_str)
            user = jwt_auth.get_user(validated_token)

            return Response({
                "user_id": str(user.id),
                "username": user.username,
                "role": user.role.name if hasattr(user, 'role') else None,
                "is_valid": True
            }, status=status.HTTP_200_OK)

        except (InvalidToken, TokenError):
            return Response(
                {"is_valid": False, "detail": "Invalid or expired token"},
                status=status.HTTP_401_UNAUTHORIZED
            )
